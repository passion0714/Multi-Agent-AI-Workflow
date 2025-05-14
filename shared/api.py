"""
API for monitoring and managing the Voice AI Agent system.
Provides endpoints for checking status, managing leads, and viewing logs.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Header, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uvicorn

from database.models import get_session, Lead, LeadStatus, LeadLog
from shared import config, utils
from shared.logging_setup import setup_logging, setup_stdlib_logging

# Set up logging
logger = setup_logging("api")
setup_stdlib_logging()

app = FastAPI(
    title="Voice AI Agent API",
    description="API for managing and monitoring the Voice AI Agent system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

# Dependency to check API key
def verify_api_key(x_api_key: str = Header(None)):
    if not config.API_KEY:
        # If no API key is configured, don't require one
        return True
    
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Model for lead creation/update
class LeadCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    area_of_interest: Optional[str] = None
    tcpa_consent: bool = False
    status: str = "Pending"
    source: Optional[str] = "API"
    additional_data: Optional[Dict[str, Any]] = None

# Model for lead response
class LeadResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    area_of_interest: Optional[str] = None
    tcpa_consent: bool = False
    status: str
    source: Optional[str] = None
    created_at: float
    updated_at: float
    call_attempts: int
    last_call_timestamp: Optional[float] = None
    entry_attempts: int
    last_entry_timestamp: Optional[float] = None

# Model for log response
class LogResponse(BaseModel):
    id: str
    lead_id: str
    timestamp: float
    action: str
    details: Optional[Dict[str, Any]] = None
    actor: str

# Model for system status
class SystemStatus(BaseModel):
    status: str = "online"
    version: str = "1.0.0"
    database_connected: bool
    voice_agent_running: bool = False
    data_entry_agent_running: bool = False
    lead_count: Dict[str, int]
    uptime: int  # Seconds
    started_at: float

# Store startup time
startup_time = utils.timestamp()

@app.get("/", response_model=SystemStatus)
async def get_status(db: Session = Depends(get_db)):
    """Get the overall system status"""
    # Check database connection
    db_connected = True
    try:
        # Try a simple query to check connection
        db.execute("SELECT 1").fetchone()
    except Exception:
        db_connected = False
    
    # Get lead counts by status
    lead_count = {}
    if db_connected:
        try:
            for status in LeadStatus:
                count = db.query(Lead).filter(Lead.status == status).count()
                lead_count[status.value] = count
        except Exception as e:
            logger.error(f"Error getting lead counts: {str(e)}")
            lead_count = {"error": "Could not retrieve lead counts"}
    
    # TODO: Add actual checks for agent status
    # This could be implemented via a heartbeat endpoint that each agent calls periodically
    
    return SystemStatus(
        database_connected=db_connected,
        lead_count=lead_count,
        uptime=int(utils.timestamp() - startup_time),
        started_at=startup_time
    )

@app.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of leads to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get a list of leads, with optional filtering"""
    query = db.query(Lead)
    
    # Apply filters
    if status:
        try:
            query = query.filter(Lead.status == LeadStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    # Get total count for the query
    total_count = query.count()
    
    # Apply pagination
    query = query.order_by(Lead.updated_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    leads = query.all()
    
    # Convert to response models
    return [LeadResponse(**lead.to_dict()) for lead in leads]

@app.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get a specific lead by ID"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return LeadResponse(**lead.to_dict())

@app.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Create a new lead"""
    # Convert status string to enum
    try:
        status = LeadStatus(lead_data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {lead_data.status}")
    
    # Create new lead
    lead = Lead(
        name=lead_data.name,
        email=lead_data.email,
        phone=utils.format_phone_number(lead_data.phone) if lead_data.phone else None,
        address=lead_data.address,
        street=lead_data.street,
        city=lead_data.city,
        state=lead_data.state,
        zip_code=lead_data.zip_code,
        area_of_interest=lead_data.area_of_interest,
        tcpa_consent=lead_data.tcpa_consent,
        status=status,
        source=lead_data.source or "API",
        additional_data=lead_data.additional_data
    )
    
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    # Log the creation
    lead.log_activity(db, "lead_created", {"source": lead_data.source or "API"}, "api")
    db.commit()
    
    return LeadResponse(**lead.to_dict())

@app.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Update an existing lead"""
    # Find the lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Convert status string to enum
    try:
        status = LeadStatus(lead_data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {lead_data.status}")
    
    # Update lead fields
    lead.name = lead_data.name
    lead.email = lead_data.email
    lead.phone = utils.format_phone_number(lead_data.phone) if lead_data.phone else None
    lead.address = lead_data.address
    lead.street = lead_data.street
    lead.city = lead_data.city
    lead.state = lead_data.state
    lead.zip_code = lead_data.zip_code
    lead.area_of_interest = lead_data.area_of_interest
    lead.tcpa_consent = lead_data.tcpa_consent
    lead.status = status
    
    # Only update additional_data if provided
    if lead_data.additional_data is not None:
        lead.additional_data = lead_data.additional_data
    
    lead.updated_at = utils.timestamp()
    
    # Log the update
    lead.log_activity(db, "lead_updated", {"source": "API"}, "api")
    
    db.commit()
    db.refresh(lead)
    
    return LeadResponse(**lead.to_dict())

@app.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Delete a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Delete the lead
    db.delete(lead)
    db.commit()
    
    return {"status": "success", "message": f"Lead {lead_id} deleted"}

@app.get("/leads/{lead_id}/logs", response_model=List[LogResponse])
async def get_lead_logs(
    lead_id: str,
    limit: int = Query(100, description="Maximum number of logs to return"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get logs for a specific lead"""
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get logs
    logs = db.query(LeadLog).filter(LeadLog.lead_id == lead_id) \
             .order_by(LeadLog.timestamp.desc()) \
             .limit(limit) \
             .all()
    
    return [LogResponse(**log.to_dict()) for log in logs]

@app.post("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    status: str = Query(..., description="New status for the lead"),
    notes: Optional[str] = Query(None, description="Optional notes about the status change"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Update the status of a lead"""
    # Find the lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Convert status string to enum
    try:
        new_status = LeadStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    # Update status
    old_status = lead.status
    lead.status = new_status
    lead.updated_at = utils.timestamp()
    
    # Add notes if provided
    if notes:
        if new_status in [LeadStatus.CALL_FAILED, LeadStatus.CONFIRMED, LeadStatus.NOT_INTERESTED]:
            lead.call_notes = notes
        elif new_status in [LeadStatus.ENTRY_FAILED, LeadStatus.ENTERED]:
            lead.entry_notes = notes
    
    # Log the status change
    lead.log_activity(
        db, 
        "status_changed", 
        {
            "old_status": old_status.value,
            "new_status": new_status.value,
            "notes": notes
        }, 
        "api"
    )
    
    db.commit()
    db.refresh(lead)
    
    return {"status": "success", "message": f"Lead status updated to {new_status.value}"}

@app.get("/stats/daily")
async def get_daily_stats(
    days: int = Query(7, description="Number of days to include"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get daily statistics for the system"""
    # Calculate the timestamp for the start date
    now = datetime.now()
    start_date = now - timedelta(days=days)
    start_timestamp = start_date.timestamp()
    
    # Initialize results
    results = []
    
    # For each day, get the stats
    for i in range(days):
        day_start = (start_date + timedelta(days=i)).timestamp()
        day_end = (start_date + timedelta(days=i+1)).timestamp()
        
        # Total new leads
        new_leads = db.query(Lead).filter(Lead.created_at >= day_start, Lead.created_at < day_end).count()
        
        # Calls made
        calls_made = db.query(Lead).filter(
            Lead.last_call_timestamp >= day_start,
            Lead.last_call_timestamp < day_end
        ).count()
        
        # Successful confirmations
        confirmations = db.query(Lead).filter(
            Lead.status == LeadStatus.CONFIRMED,
            Lead.updated_at >= day_start,
            Lead.updated_at < day_end
        ).count()
        
        # Data entries made
        entries_made = db.query(Lead).filter(
            Lead.last_entry_timestamp >= day_start,
            Lead.last_entry_timestamp < day_end
        ).count()
        
        # Successful entries
        successful_entries = db.query(Lead).filter(
            Lead.status == LeadStatus.ENTERED,
            Lead.updated_at >= day_start,
            Lead.updated_at < day_end
        ).count()
        
        day_stats = {
            "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "new_leads": new_leads,
            "calls_made": calls_made,
            "confirmations": confirmations,
            "entries_made": entries_made,
            "successful_entries": successful_entries
        }
        
        results.append(day_stats)
    
    return results

def start_api():
    """Start the API server"""
    uvicorn.run(
        "shared.api:app", 
        host=config.API_HOST, 
        port=config.API_PORT,
        reload=config.is_development_mode()
    )

if __name__ == "__main__":
    start_api() 