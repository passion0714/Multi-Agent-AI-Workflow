import os
import sys
from pathlib import Path
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database.repository import LeadRepository
from app.database.models import LeadStatus
from app.utils.csv_processor import CSVProcessor
from app.config.settings import APP_NAME, APP_VERSION, CSV_IMPORT_DIRECTORY

# Create FastAPI app
app = FastAPI(
    title=f"{APP_NAME} API",
    description="API for the Multi-Agent Lead Processing System",
    version=APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Models -----

class LeadBase(BaseModel):
    firstname: str
    lastname: str
    email: str
    phone1: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None


class LeadCreate(LeadBase):
    education_level: Optional[str] = None
    area_of_study: Optional[str] = None
    

class LeadResponse(LeadBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True


# ----- Routes -----

@app.get("/", tags=["General"])
async def root():
    """Get basic API information"""
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status", tags=["General"])
async def get_status():
    """Get system status and statistics"""
    stats = LeadRepository.get_lead_statistics()
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "statistics": stats
    }


@app.get("/leads", tags=["Leads"], response_model=List[LeadResponse])
async def get_leads(status: Optional[str] = None, limit: int = 100, offset: int = 0):
    """
    Get a list of leads, optionally filtered by status.
    
    Parameters:
    -----------
    status : Optional[str]
        Filter by lead status. If None, get all leads.
    limit : int
        Maximum number of leads to return. Default is 100.
    offset : int
        Offset for pagination. Default is 0.
    """
    try:
        if status:
            try:
                lead_status = LeadStatus[status.upper()]
                leads = LeadRepository.get_leads_by_status(lead_status, limit=limit)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        else:
            # Get all leads (this would need to be implemented)
            # Simplified implementation for demonstration
            leads = []
            
            for status_enum in LeadStatus:
                leads.extend(LeadRepository.get_leads_by_status(status_enum, limit=limit//len(LeadStatus)))
        
        # Convert to response model
        return [
            LeadResponse(
                id=lead.id,
                firstname=lead.firstname,
                lastname=lead.lastname,
                email=lead.email,
                phone1=lead.phone1,
                address=lead.address,
                city=lead.city,
                state=lead.state,
                zip=lead.zip,
                status=lead.status.value,
                created_at=lead.created_at
            )
            for lead in leads
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads/{lead_id}", tags=["Leads"], response_model=LeadResponse)
async def get_lead(lead_id: int):
    """
    Get a lead by ID.
    
    Parameters:
    -----------
    lead_id : int
        The ID of the lead to retrieve.
    """
    try:
        lead = LeadRepository.get_lead_by_id(lead_id)
        
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
        return LeadResponse(
            id=lead.id,
            firstname=lead.firstname,
            lastname=lead.lastname,
            email=lead.email,
            phone1=lead.phone1,
            address=lead.address,
            city=lead.city,
            state=lead.state,
            zip=lead.zip,
            status=lead.status.value,
            created_at=lead.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/leads", tags=["Leads"], response_model=LeadResponse)
async def create_lead(lead: LeadCreate):
    """
    Create a new lead.
    
    Parameters:
    -----------
    lead : LeadCreate
        The lead data to create.
    """
    try:
        # Convert to dictionary
        lead_data = lead.dict()
        
        # Set default status
        lead_data["status"] = LeadStatus.PENDING
        
        # Create the lead
        lead_id = LeadRepository.create_lead(lead_data)
        
        if not lead_id:
            raise HTTPException(status_code=500, detail="Failed to create lead")
        
        # Retrieve the created lead
        created_lead = LeadRepository.get_lead_by_id(lead_id)
        
        return LeadResponse(
            id=created_lead.id,
            firstname=created_lead.firstname,
            lastname=created_lead.lastname,
            email=created_lead.email,
            phone1=created_lead.phone1,
            address=created_lead.address,
            city=created_lead.city,
            state=created_lead.state,
            zip=created_lead.zip,
            status=created_lead.status.value,
            created_at=created_lead.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/leads/{lead_id}/status", tags=["Leads"])
async def update_lead_status(lead_id: int, status: str):
    """
    Update the status of a lead.
    
    Parameters:
    -----------
    lead_id : int
        The ID of the lead to update.
    status : str
        The new status for the lead.
    """
    try:
        # Validate status
        try:
            lead_status = LeadStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Update the lead status
        success = LeadRepository.update_lead_status(lead_id, lead_status)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
        return {"status": "success", "message": f"Lead {lead_id} status updated to {status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/csv/upload", tags=["CSV"])
async def upload_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a CSV file for processing.
    
    Parameters:
    -----------
    file : UploadFile
        The CSV file to upload.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Create destination path
        os.makedirs(CSV_IMPORT_DIRECTORY, exist_ok=True)
        destination = os.path.join(CSV_IMPORT_DIRECTORY, file.filename)
        
        # Check if file already exists
        if os.path.exists(destination):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename, ext = os.path.splitext(file.filename)
            destination = os.path.join(CSV_IMPORT_DIRECTORY, f"{filename}_{timestamp}{ext}")
        
        # Write the file
        with open(destination, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process the file in the background
        def process_csv():
            CSVProcessor.import_csv_file(destination)
        
        background_tasks.add_task(process_csv)
        
        return {
            "status": "success", 
            "message": f"File {file.filename} uploaded successfully and scheduled for processing",
            "file_path": destination
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/csv/process", tags=["CSV"])
async def process_csv_files(background_tasks: BackgroundTasks):
    """
    Manually trigger processing of all CSV files in the import directory.
    """
    try:
        # Process CSV files in the background
        def process_csv():
            results = CSVProcessor.process_new_csv_files()
            return results
        
        background_tasks.add_task(process_csv)
        
        return {
            "status": "success", 
            "message": "CSV processing scheduled",
            "import_directory": CSV_IMPORT_DIRECTORY
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the API server
def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the API server.
    
    Parameters:
    -----------
    host : str
        The host to listen on. Default is "0.0.0.0".
    port : int
        The port to listen on. Default is 8000.
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="API Server for Multi-Agent Lead Processing System")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to listen on")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()
    
    # Start the API server
    start_api_server(host=args.host, port=args.port) 