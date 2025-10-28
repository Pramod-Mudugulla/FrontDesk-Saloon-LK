from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column


Base = declarative_base()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)

    call_sessions: Mapped[list["CallSession"]] = relationship("CallSession", back_populates="customer")
    help_requests: Mapped[list["HelpRequest"]] = relationship("HelpRequest", back_populates="customer")


class CallSession(Base, TimestampMixin):
    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="call_sessions")

    __table_args__ = (
        UniqueConstraint("room_name", name="uq_call_sessions_room_name"),
    )


class HelpRequestStatus:
    PENDING = "pending"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class HelpRequest(Base, TimestampMixin):
    __tablename__ = "help_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("call_sessions.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default=HelpRequestStatus.PENDING, nullable=False, index=True)
    timeout_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    resolved_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship("Customer", back_populates="help_requests")
    call_session: Mapped[CallSession] = relationship("CallSession")
    supervisor_responses: Mapped[list["SupervisorResponse"]] = relationship(
        "SupervisorResponse", back_populates="help_request", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_help_requests_status_timeout", "status", "timeout_at"),
    )


class SupervisorResponse(Base, TimestampMixin):
    __tablename__ = "supervisor_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    help_request_id: Mapped[int] = mapped_column(Integer, ForeignKey("help_requests.id"), nullable=False, index=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    supervisor_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    help_request: Mapped[HelpRequest] = relationship("HelpRequest", back_populates="supervisor_responses")


class KnowledgeEntry(Base, TimestampMixin):
    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_canonical: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    source_help_request_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("help_requests.id"), nullable=True)

    __table_args__ = (
        Index("ix_knowledge_question", "question_canonical"),
    )


