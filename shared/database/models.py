"""
Database models for the Voice AI Agent system.

This module defines the SQLAlchemy ORM models representing the database schema
for the Voice AI Agent system, including Lead, Call, and other related models.
"""

import sys
import enum
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, 
    Enum, ForeignKey, JSON, Table, UniqueConstraint, Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from shared.config import load_config

# Load configuration
config = load_config()

# Create base class for declarative models
Base = declarative_base()

# Create engine with connection pool
engine = create_engine(
    "postgresql://postgres:123@127.0.0.1:5432/multiagent_db",  # Hardcoded for now to ensure correct values
    pool_size=int(config.get('DB_POOL_SIZE', 5)),
    max_overflow=int(config.get('DB_MAX_OVERFLOW', 10)),
    pool_timeout=int(config.get('DB_POOL_TIMEOUT', 30)),
    pool_recycle=int(config.get('DB_POOL_RECYCLE', 1800)),
)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def get_session():
    """Get a new database session."""
    return Session()


# Enum definitions for various status fields
class LeadStatus(enum.Enum):
    """Status of a lead in the system."""
    NEW = 'new'
    ASSIGNED = 'assigned'
    SCHEDULED = 'scheduled'
    IN_PROGRESS = 'in_progress'
    CALL_ATTEMPTED = 'call_attempted'
    CALL_CONNECTED = 'call_connected'
    CALL_FAILED = 'call_failed'
    CONFIRMED = 'confirmed'
    ENTRY_IN_PROGRESS = 'entry_in_progress' 
    ENTERED = 'entered'
    ENTRY_FAILED = 'entry_failed'
    NOT_INTERESTED = 'not_interested'
    DUPLICATE = 'duplicate'
    INVALID = 'invalid'
    COMPLETED = 'completed'
    ERROR = 'error'


class CallStatus(enum.Enum):
    """Status of an outbound call."""
    SCHEDULED = 'scheduled'
    INITIATED = 'initiated'
    CONNECTING = 'connecting'
    CONNECTED = 'connected'
    COMPLETED = 'completed'
    FAILED = 'failed'
    BUSY = 'busy'
    NO_ANSWER = 'no_answer'
    VOICEMAIL = 'voicemail'


class CallOutcome(enum.Enum):
    """Outcome of a completed call."""
    CONFIRMED = 'confirmed'
    NOT_INTERESTED = 'not_interested'
    NO_DECISION = 'no_decision'
    CALL_BACK = 'call_back'
    WRONG_NUMBER = 'wrong_number'
    HANG_UP = 'hang_up'
    TECHNICAL_ISSUE = 'technical_issue'


# Models
class Lead(Base):
    """
    Lead model representing a potential customer to be contacted.
    
    A lead has contact information, status tracking, and relationships
    to calls and other relevant data.
    """
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(255), index=True, nullable=True)
    source = Column(String(100), nullable=False, default='manual')
    
    # Contact information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=False, index=True)
    alt_phone = Column(String(20), nullable=True)
    
    # Address
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(20), nullable=True)
    
    # Status tracking
    status = Column(Enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    
    # Additional details
    area_of_interest = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Call tracking
    call_attempts = Column(Integer, nullable=False, default=0)
    last_call_timestamp = Column(DateTime, nullable=True)
    next_call_timestamp = Column(DateTime, nullable=True)
    
    # Data entry tracking
    entry_attempts = Column(Integer, nullable=False, default=0)
    last_entry_timestamp = Column(DateTime, nullable=True)
    entry_duration = Column(Float, nullable=True)
    entry_notes = Column(Text, nullable=True)
    
    # Locking mechanism
    locked_until = Column(DateTime, nullable=True)
    locked_by = Column(String(100), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # TCPA compliance
    is_tcpa_compliant = Column(Boolean, nullable=False, default=False)
    tcpa_timestamp = Column(DateTime, nullable=True)
    tcpa_source = Column(String(100), nullable=True)
    
    # Relationships
    calls = relationship("Call", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_lead_status_locked', 'status', 'locked_until'),
        Index('idx_lead_next_call', 'next_call_timestamp', 'status'),
    )
    
    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.first_name} {self.last_name}', status={self.status})>"
    
    @property
    def name(self):
        """Full name of the lead."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert lead to dictionary representation."""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'source': self.source,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'alt_phone': self.alt_phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'area_of_interest': self.area_of_interest,
            'notes': self.notes,
            'additional_data': self.additional_data,
            'call_attempts': self.call_attempts,
            'last_call_timestamp': self.last_call_timestamp.isoformat() if self.last_call_timestamp else None,
            'next_call_timestamp': self.next_call_timestamp.isoformat() if self.next_call_timestamp else None,
            'entry_attempts': self.entry_attempts,
            'last_entry_timestamp': self.last_entry_timestamp.isoformat() if self.last_entry_timestamp else None,
            'entry_duration': self.entry_duration,
            'entry_notes': self.entry_notes,
            'is_tcpa_compliant': self.is_tcpa_compliant,
            'tcpa_timestamp': self.tcpa_timestamp.isoformat() if self.tcpa_timestamp else None,
            'tcpa_source': self.tcpa_source
        }
    
    def log_activity(self, session, activity_type, activity_data=None, actor=None):
        """
        Log an activity for this lead.
        
        Args:
            session: Database session
            activity_type: Type of activity
            activity_data: Optional data related to the activity
            actor: Who/what performed the activity
        """
        activity = LeadActivity(
            lead_id=self.id,
            activity_type=activity_type,
            activity_data=activity_data,
            actor=actor
        )
        session.add(activity)
        return activity


class Call(Base):
    """
    Call model representing an outbound call to a lead.
    
    Tracks the entire lifecycle of a call, including scheduling,
    initiation, connection, and outcome.
    """
    __tablename__ = 'calls'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False, index=True)
    
    # Call details
    phone_number = Column(String(20), nullable=False)
    call_id = Column(String(100), nullable=True, index=True)  # External call ID from provider
    provider = Column(String(50), nullable=True)  # Voice API provider used
    
    # Status tracking
    status = Column(Enum(CallStatus), nullable=False, default=CallStatus.SCHEDULED)
    outcome = Column(Enum(CallOutcome), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    scheduled_at = Column(DateTime, nullable=True)
    initiated_at = Column(DateTime, nullable=True)
    connected_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Call data
    duration = Column(Integer, nullable=True)  # in seconds
    recording_url = Column(String(255), nullable=True)
    transcript = Column(Text, nullable=True)
    call_data = Column(JSON, nullable=True)  # Additional data from the call
    
    # Notes and analysis
    notes = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="calls")
    conversation_turns = relationship("ConversationTurn", back_populates="call", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Call(id={self.id}, lead_id={self.lead_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert call to dictionary representation."""
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'phone_number': self.phone_number,
            'call_id': self.call_id,
            'provider': self.provider,
            'status': self.status.value if self.status else None,
            'outcome': self.outcome.value if self.outcome else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'recording_url': self.recording_url,
            'transcript': self.transcript,
            'call_data': self.call_data,
            'notes': self.notes,
            'sentiment_score': self.sentiment_score
        }


class ConversationTurn(Base):
    """
    ConversationTurn model representing a single turn in a conversation.
    
    A turn is either the agent speaking or the lead responding.
    """
    __tablename__ = 'conversation_turns'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey('calls.id'), nullable=False, index=True)
    
    # Turn details
    turn_index = Column(Integer, nullable=False)  # Sequential index within the call
    speaker = Column(String(20), nullable=False)  # 'agent' or 'lead'
    text = Column(Text, nullable=False)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Analysis
    intent = Column(String(100), nullable=True)  # Detected intent
    sentiment_score = Column(Float, nullable=True)
    analysis_data = Column(JSON, nullable=True)  # Additional analysis data
    
    # Relationships
    call = relationship("Call", back_populates="conversation_turns")
    
    __table_args__ = (
        UniqueConstraint('call_id', 'turn_index', name='uq_call_turn_index'),
    )
    
    def __repr__(self):
        return f"<ConversationTurn(id={self.id}, call_id={self.call_id}, turn_index={self.turn_index})>"


class LeadActivity(Base):
    """
    LeadActivity model for tracking all activities related to a lead.
    
    Used for audit trail and analytics.
    """
    __tablename__ = 'lead_activities'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)
    activity_data = Column(JSON, nullable=True)
    actor = Column(String(100), nullable=True)  # Who/what performed the activity
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    
    def __repr__(self):
        return f"<LeadActivity(id={self.id}, lead_id={self.lead_id}, activity_type={self.activity_type})>"


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)


def drop_db():
    """Drop all tables from the database."""
    Base.metadata.drop_all(engine)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        print("Initializing database...")
        init_db()
        print("Database initialized.")
    elif len(sys.argv) > 1 and sys.argv[1] == "drop":
        print("WARNING: This will drop all tables. Are you sure? (y/n)")
        if input().lower() == 'y':
            print("Dropping database tables...")
            drop_db()
            print("Database tables dropped.")
    else:
        print("Usage: python models.py [init|drop]") 