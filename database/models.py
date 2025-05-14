"""
SQLAlchemy models for the shared data store.
These models define the schema for the database that will be used as the
communication hub between the Voice Agent and Data Entry Agent.
"""

from typing import Optional, Dict, Any, List
import enum
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Enum, 
    Text, JSON, DateTime, ForeignKey, Table, create_engine, MetaData
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
import json

from shared import config, utils

# Create the base class
Base = declarative_base()

# Define an enum for lead status
class LeadStatus(enum.Enum):
    PENDING = "Pending"               # Initial state, ready to be called
    CALLING = "Calling"               # Voice agent is actively calling
    CALL_FAILED = "Call Failed"       # Call could not be completed (no answer, busy, etc.)
    CONFIRMED = "Confirmed"           # Lead data confirmed by call
    NOT_INTERESTED = "Not Interested" # Lead is not interested
    ENTRY_IN_PROGRESS = "Entry in Progress" # Data entry agent is entering data
    ENTERED = "Entered"               # Data entry completed successfully
    ENTRY_FAILED = "Entry Failed"     # Data entry failed
    DUPLICATE = "Duplicate"           # Lead is a duplicate of another lead
    ERROR = "Error"                   # Error occurred during processing

# Define a model for our leads
class Lead(Base):
    """Model for lead data"""
    __tablename__ = 'leads'
    
    id = Column(String(36), primary_key=True, default=utils.generate_id)
    
    # Basic lead information (initially from CSV)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)  
    address = Column(Text, nullable=True)
    
    # Address components (may be extracted from full address)
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    
    # Area of interest
    area_of_interest = Column(String(100), nullable=True)
    
    # TCPA opt-in status
    tcpa_consent = Column(Boolean, default=False)
    
    # Tracking fields
    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING)
    source = Column(String(50), nullable=True)  # e.g., "CSV Import", "API", etc.
    created_at = Column(Float, default=utils.timestamp)
    updated_at = Column(Float, default=utils.timestamp, onupdate=utils.timestamp)
    
    # Voice Agent related fields
    call_attempts = Column(Integer, default=0)
    last_call_timestamp = Column(Float, nullable=True)
    call_duration = Column(Float, nullable=True)  # Duration in seconds
    call_notes = Column(Text, nullable=True)
    voice_consent_recording_url = Column(String(255), nullable=True)
    
    # Data Entry related fields
    entry_attempts = Column(Integer, default=0)
    last_entry_timestamp = Column(Float, nullable=True)
    entry_duration = Column(Float, nullable=True)  # Duration in seconds
    entry_notes = Column(Text, nullable=True)
    
    # JSON fields for additional data
    original_data = Column(JSON, nullable=True)  # Original data from import
    voice_data = Column(JSON, nullable=True)     # Data collected during voice call
    additional_data = Column(JSON, nullable=True) # Any additional data
    
    # Relationships
    logs = relationship("LeadLog", back_populates="lead", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lead to dictionary representation"""
        result = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "area_of_interest": self.area_of_interest,
            "tcpa_consent": self.tcpa_consent,
            "status": self.status.value if self.status else None,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "call_attempts": self.call_attempts,
            "last_call_timestamp": self.last_call_timestamp,
            "call_duration": self.call_duration,
            "call_notes": self.call_notes,
            "voice_consent_recording_url": self.voice_consent_recording_url,
            "entry_attempts": self.entry_attempts,
            "last_entry_timestamp": self.last_entry_timestamp,
            "entry_duration": self.entry_duration,
            "entry_notes": self.entry_notes,
        }
        
        # Handle JSON fields
        if self.original_data:
            result["original_data"] = self.original_data
        if self.voice_data:
            result["voice_data"] = self.voice_data
        if self.additional_data:
            result["additional_data"] = self.additional_data
            
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update lead from dictionary data"""
        for key, value in data.items():
            if hasattr(self, key) and key != 'id':
                if key == 'status' and isinstance(value, str):
                    self.status = LeadStatus(value)
                else:
                    setattr(self, key, value)
        
        # Update the updated_at timestamp
        self.updated_at = utils.timestamp()
    
    def log_activity(self, session: Session, action: str, details: Optional[Dict[str, Any]] = None,
                    actor: str = "system") -> "LeadLog":
        """Add a log entry for this lead"""
        log = LeadLog(
            lead_id=self.id,
            action=action,
            details=details,
            actor=actor
        )
        session.add(log)
        return log
    
    def __repr__(self) -> str:
        return f"<Lead(id='{self.id}', name='{self.name}', status='{self.status.value if self.status else None}')>"


class LeadLog(Base):
    """Model for lead activity logs"""
    __tablename__ = 'lead_logs'
    
    id = Column(String(36), primary_key=True, default=utils.generate_id)
    lead_id = Column(String(36), ForeignKey('leads.id'), nullable=False)
    timestamp = Column(Float, default=utils.timestamp)
    action = Column(String(50), nullable=False)  # e.g., "call_initiated", "data_updated", etc.
    details = Column(JSON, nullable=True)
    actor = Column(String(50), default="system")  # e.g., "voice_agent", "data_entry_agent", "user"
    
    # Relationship back to lead
    lead = relationship("Lead", back_populates="logs")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log to dictionary representation"""
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "details": self.details,
            "actor": self.actor
        }
    
    def __repr__(self) -> str:
        return f"<LeadLog(lead_id='{self.lead_id}', action='{self.action}')>"


# Create a database connection engine
def get_engine():
    """Get the SQLAlchemy engine"""
    db_config = config.get_database_config()
    return create_engine(db_config["url"], 
                         echo=db_config["echo"],
                         pool_size=db_config.get("pool_size"),
                         pool_timeout=db_config.get("pool_timeout"),
                         pool_recycle=db_config.get("pool_recycle"))


# Session factory
def get_session() -> Session:
    """Create a new database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# Create all tables in the database
def init_db():
    """Initialize the database by creating all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine 