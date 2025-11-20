from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from .client import Base


class Customer(Base):
    """Customer/User model for storing user profile information"""
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Profile information
    age = Column(Integer, nullable=True)
    sex = Column(String(20), nullable=True)  # male, female, other
    diabetes = Column(Boolean, default=False, nullable=False)
    hypertension = Column(Boolean, default=False, nullable=False)
    pregnancy = Column(Boolean, default=False, nullable=False)
    city = Column(String(100), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)  # Store additional profile data
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="customer", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customer to dictionary"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "age": self.age,
            "sex": self.sex,
            "diabetes": self.diabetes,
            "hypertension": self.hypertension,
            "pregnancy": self.pregnancy,
            "city": self.city,
            "metadata": self.metadata,
        }
    
    def __repr__(self):
        return f"<Customer(id={self.id}, age={self.age}, city={self.city})>"


class ChatSession(Base):
    """Chat session model for grouping related chat messages"""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Session metadata
    language = Column(String(10), nullable=True)  # en, hi, ta, te, kn, ml
    session_metadata = Column(JSON, nullable=True)  # Store session-level metadata
    
    # Relationships
    customer = relationship("Customer", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    
    # Indexes
    __table_args__ = (
        Index("idx_chat_sessions_customer_created", "customer_id", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "language": self.language,
            "session_metadata": self.session_metadata,
            "message_count": len(self.messages) if self.messages else 0,
        }
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, customer_id={self.customer_id}, language={self.language})>"


class ChatMessage(Base):
    """Chat message model for storing individual chat messages"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant
    message_text = Column(Text, nullable=False)
    language = Column(String(10), nullable=True)  # en, hi, ta, te, kn, ml
    
    # Response data
    route = Column(String(20), nullable=True)  # graph, vector
    answer = Column(Text, nullable=True)  # Assistant's response
    
    # Safety and facts
    safety_data = Column(JSON, nullable=True)  # Store safety analysis results
    facts = Column(JSON, nullable=True)  # Store facts array
    citations = Column(JSON, nullable=True)  # Store citations array
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Store timings, debug info, etc.
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_chat_messages_session_created", "session_id", "created_at"),
        Index("idx_chat_messages_role", "role"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "role": self.role,
            "message_text": self.message_text,
            "language": self.language,
            "route": self.route,
            "answer": self.answer,
            "safety_data": self.safety_data,
            "facts": self.facts,
            "citations": self.citations,
            "metadata": self.metadata,
        }
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"












