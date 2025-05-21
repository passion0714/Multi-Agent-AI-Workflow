from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class LeadStatus(enum.Enum):
    PENDING = "pending"
    CALLING = "calling"
    CONFIRMED = "confirmed"
    NOT_INTERESTED = "not_interested"
    CALL_FAILED = "call_failed"
    ENTRY_IN_PROGRESS = "entry_in_progress"
    ENTERED = "entered"
    ENTRY_FAILED = "entry_failed"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    
    # Basic information from CSV
    firstname = Column(String(100))
    lastname = Column(String(100))
    email = Column(String(255))
    phone1 = Column(String(20))
    address = Column(String(255))
    address2 = Column(String(255), nullable=True)
    city = Column(String(100))
    state = Column(String(50))
    zip = Column(String(20))
    gender = Column(String(10), nullable=True)
    dob = Column(String(20), nullable=True)
    ip = Column(String(50), nullable=True)
    subid_2 = Column(String(50), nullable=True)
    signup_url = Column(String(255), nullable=True)
    consent_url = Column(String(255), nullable=True)
    education_level = Column(String(100), nullable=True)
    grad_year = Column(String(20), nullable=True)
    start_date = Column(String(100), nullable=True)
    military_type = Column(String(100), nullable=True)
    campus_type = Column(String(100), nullable=True)
    area_of_study = Column(String(100), nullable=True)
    level_of_interest = Column(String(50), nullable=True)
    computer_with_internet = Column(String(10), nullable=True)
    us_citizen = Column(String(10), nullable=True)
    registered_nurse = Column(String(10), nullable=True)
    teaching_license = Column(String(10), nullable=True)
    enroll_status = Column(String(50), nullable=True)
    
    # Additional fields that may be updated during the voice call
    confirmed_address = Column(String(255), nullable=True)
    confirmed_email = Column(String(255), nullable=True)
    confirmed_phone = Column(String(20), nullable=True)
    confirmed_area_of_interest = Column(String(100), nullable=True)
    tcpa_accepted = Column(Boolean, nullable=True)
    
    # Workflow and tracking fields
    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING)
    status_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Call information
    call_initiated_at = Column(DateTime, nullable=True)
    call_completed_at = Column(DateTime, nullable=True)
    call_duration = Column(Integer, nullable=True)  # Duration in seconds
    call_recording_url = Column(String(255), nullable=True)
    call_notes = Column(Text, nullable=True)
    call_attempts = Column(Integer, default=0)
    
    # Data entry information
    entry_initiated_at = Column(DateTime, nullable=True)
    entry_completed_at = Column(DateTime, nullable=True)
    entry_duration = Column(Integer, nullable=True)  # Duration in seconds
    entry_notes = Column(Text, nullable=True)
    entry_attempts = Column(Integer, default=0)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Relationships
    call_logs = relationship("CallLog", back_populates="lead")
    entry_logs = relationship("EntryLog", back_populates="lead")
    
    def __repr__(self):
        return f"<Lead {self.id}: {self.firstname} {self.lastname} - {self.status.value}>"


class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    status = Column(String(50))  # 'completed', 'failed', 'no-answer', etc.
    recording_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationship
    lead = relationship("Lead", back_populates="call_logs")
    
    def __repr__(self):
        return f"<CallLog {self.id} for Lead {self.lead_id}: {self.status}>"


class EntryLog(Base):
    __tablename__ = "entry_logs"
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    status = Column(String(50))  # 'completed', 'failed', etc.
    notes = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationship
    lead = relationship("Lead", back_populates="entry_logs")
    
    def __repr__(self):
        return f"<EntryLog {self.id} for Lead {self.lead_id}: {self.status}>"


# Create database connection
def get_db_url():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "lead_processing")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


# For direct DB operations when needed
engine = create_engine(get_db_url()) 