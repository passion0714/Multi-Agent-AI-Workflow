from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.database.models import Lead, LeadStatus, CallLog, EntryLog
from app.database.session import get_db_session
from loguru import logger


class LeadRepository:
    """
    Repository class for performing database operations on leads.
    """
    
    @staticmethod
    def get_lead_by_id(lead_id: int) -> Optional[Lead]:
        """
        Get a lead by its ID.
        
        Parameters:
        -----------
        lead_id : int
            The ID of the lead to retrieve.
            
        Returns:
        --------
        Optional[Lead]
            The lead object if found, None otherwise.
        """
        with get_db_session() as session:
            return session.query(Lead).filter(Lead.id == lead_id).first()
    
    @staticmethod
    def get_leads_by_status(status: LeadStatus, limit: int = 100) -> List[Lead]:
        """
        Get leads by their status.
        
        Parameters:
        -----------
        status : LeadStatus
            The status to filter leads by.
        limit : int, optional
            The maximum number of leads to return. Default is 100.
            
        Returns:
        --------
        List[Lead]
            A list of leads with the specified status.
        """
        with get_db_session() as session:
            return session.query(Lead).filter(Lead.status == status).limit(limit).all()
    
    @staticmethod
    def get_pending_leads_for_calling(limit: int = 10) -> List[Lead]:
        """
        Get pending leads that are ready to be called.
        
        Parameters:
        -----------
        limit : int, optional
            The maximum number of leads to return. Default is 10.
            
        Returns:
        --------
        List[Lead]
            A list of pending leads ready for calling.
        """
        with get_db_session() as session:
            # Get leads that are in PENDING status and haven't been called yet or haven't been called in the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            return session.query(Lead).filter(
                and_(
                    Lead.status == LeadStatus.PENDING,
                    or_(
                        Lead.call_initiated_at == None,
                        Lead.call_initiated_at < one_hour_ago
                    ),
                    Lead.call_attempts < 3  # Limit attempts
                )
            ).order_by(Lead.created_at).limit(limit).all()
    
    @staticmethod
    def get_confirmed_leads_for_entry(limit: int = 10) -> List[Lead]:
        """
        Get confirmed leads that are ready for data entry.
        
        Parameters:
        -----------
        limit : int, optional
            The maximum number of leads to return. Default is 10.
            
        Returns:
        --------
        List[Lead]
            A list of confirmed leads ready for data entry.
        """
        with get_db_session() as session:
            # Get leads that are in CONFIRMED status
            return session.query(Lead).filter(
                and_(
                    Lead.status == LeadStatus.CONFIRMED,
                    Lead.entry_attempts < 3  # Limit attempts
                )
            ).order_by(Lead.status_updated_at).limit(limit).all()
    
    @staticmethod
    def update_lead_status(lead_id: int, status: LeadStatus, additional_fields: Dict[str, Any] = None) -> bool:
        """
        Update the status of a lead.
        
        Parameters:
        -----------
        lead_id : int
            The ID of the lead to update.
        status : LeadStatus
            The new status for the lead.
        additional_fields : Dict[str, Any], optional
            Additional fields to update. Default is None.
            
        Returns:
        --------
        bool
            True if the update was successful, False otherwise.
        """
        try:
            with get_db_session() as session:
                lead = session.query(Lead).filter(Lead.id == lead_id).first()
                
                if not lead:
                    logger.error(f"Lead with ID {lead_id} not found for status update.")
                    return False
                
                lead.status = status
                lead.status_updated_at = datetime.utcnow()
                
                if additional_fields:
                    for key, value in additional_fields.items():
                        if hasattr(lead, key):
                            setattr(lead, key, value)
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating lead status: {str(e)}")
            return False
    
    @staticmethod
    def create_lead(lead_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new lead.
        
        Parameters:
        -----------
        lead_data : Dict[str, Any]
            The data for the new lead.
            
        Returns:
        --------
        Optional[int]
            The ID of the newly created lead if successful, None otherwise.
        """
        try:
            with get_db_session() as session:
                lead = Lead(**lead_data)
                session.add(lead)
                session.commit()
                return lead.id
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            return None
    
    @staticmethod
    def bulk_create_leads(leads_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Create multiple leads at once.
        
        Parameters:
        -----------
        leads_data : List[Dict[str, Any]]
            A list of lead data dictionaries.
            
        Returns:
        --------
        Tuple[int, int]
            A tuple containing (success_count, failure_count).
        """
        success_count = 0
        failure_count = 0
        
        with get_db_session() as session:
            try:
                for lead_data in leads_data:
                    try:
                        lead = Lead(**lead_data)
                        session.add(lead)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error adding lead to batch: {str(e)}")
                        failure_count += 1
                
                session.commit()
            except Exception as e:
                logger.error(f"Error in bulk lead creation: {str(e)}")
                session.rollback()
                # If we hit an error after some successful adds, count them as failures
                failure_count += success_count
                success_count = 0
        
        return success_count, failure_count
    
    @staticmethod
    def log_call(lead_id: int, call_data: Dict[str, Any]) -> Optional[int]:
        """
        Log a call for a lead.
        
        Parameters:
        -----------
        lead_id : int
            The ID of the lead the call is for.
        call_data : Dict[str, Any]
            Data about the call.
            
        Returns:
        --------
        Optional[int]
            The ID of the call log if successful, None otherwise.
        """
        try:
            with get_db_session() as session:
                call_log = CallLog(lead_id=lead_id, **call_data)
                session.add(call_log)
                session.commit()
                return call_log.id
        except Exception as e:
            logger.error(f"Error logging call: {str(e)}")
            return None
    
    @staticmethod
    def log_entry(lead_id: int, entry_data: Dict[str, Any]) -> Optional[int]:
        """
        Log a data entry attempt for a lead.
        
        Parameters:
        -----------
        lead_id : int
            The ID of the lead the entry is for.
        entry_data : Dict[str, Any]
            Data about the entry.
            
        Returns:
        --------
        Optional[int]
            The ID of the entry log if successful, None otherwise.
        """
        try:
            with get_db_session() as session:
                entry_log = EntryLog(lead_id=lead_id, **entry_data)
                session.add(entry_log)
                session.commit()
                return entry_log.id
        except Exception as e:
            logger.error(f"Error logging entry: {str(e)}")
            return None
    
    @staticmethod
    def get_lead_statistics() -> Dict[str, Any]:
        """
        Get statistics about leads in the system.
        
        Returns:
        --------
        Dict[str, Any]
            A dictionary containing various statistics.
        """
        stats = {
            "total_leads": 0,
            "status_counts": {},
            "calls_today": 0,
            "entries_today": 0,
            "success_rate": 0.0,
        }
        
        try:
            with get_db_session() as session:
                # Total leads
                stats["total_leads"] = session.query(func.count(Lead.id)).scalar()
                
                # Leads by status
                status_counts = session.query(
                    Lead.status, func.count(Lead.id)
                ).group_by(Lead.status).all()
                
                for status, count in status_counts:
                    stats["status_counts"][status.value] = count
                
                # Calls today
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                stats["calls_today"] = session.query(func.count(CallLog.id)).filter(
                    CallLog.initiated_at >= today_start
                ).scalar()
                
                # Entries today
                stats["entries_today"] = session.query(func.count(EntryLog.id)).filter(
                    EntryLog.initiated_at >= today_start
                ).scalar()
                
                # Success rate (leads entered / leads confirmed)
                confirmed_count = stats["status_counts"].get("confirmed", 0) + stats["status_counts"].get("entered", 0)
                entered_count = stats["status_counts"].get("entered", 0)
                
                if confirmed_count > 0:
                    stats["success_rate"] = (entered_count / confirmed_count) * 100
                
                return stats
        except Exception as e:
            logger.error(f"Error getting lead statistics: {str(e)}")
            return stats 