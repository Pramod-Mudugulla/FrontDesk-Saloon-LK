from datetime import datetime, timedelta
from typing import Optional, Iterable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .models import (
    Base,
    Customer,
    CallSession,
    HelpRequest,
    HelpRequestStatus,
    SupervisorResponse,
    KnowledgeEntry,
)
from .session import get_engine


def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def create_or_get_customer(session: Session, *, external_id: Optional[str], display_name: Optional[str], phone_number: Optional[str]) -> Customer:
    if external_id:
        existing = session.execute(select(Customer).where(Customer.external_id == external_id)).scalar_one_or_none()
        if existing:
            return existing
    customer = Customer(external_id=external_id, display_name=display_name, phone_number=phone_number)
    session.add(customer)
    session.flush()
    return customer


def create_call_session(session: Session, *, room_name: str, customer: Customer) -> CallSession:
    existing = session.execute(select(CallSession).where(CallSession.room_name == room_name)).scalar_one_or_none()
    if existing:
        return existing
    cs = CallSession(room_name=room_name, customer_id=customer.id)
    session.add(cs)
    session.flush()
    return cs


def create_help_request(
    session: Session,
    *,
    call_session: CallSession,
    customer: Customer,
    question: str,
    timeout_minutes: int = 15,
) -> HelpRequest:
    timeout_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
    hr = HelpRequest(
        call_session_id=call_session.id,
        customer_id=customer.id,
        question=question,
        status=HelpRequestStatus.PENDING,
        timeout_at=timeout_at,
    )
    session.add(hr)
    session.flush()
    return hr


def resolve_help_request(session: Session, *, help_request: HelpRequest, answer: str, supervisor_id: Optional[str]) -> SupervisorResponse:
    help_request.status = HelpRequestStatus.RESOLVED
    help_request.resolved_answer = answer
    response = SupervisorResponse(help_request_id=help_request.id, answer=answer, supervisor_id=supervisor_id)
    session.add(response)
    # Learn into KB
    kb = KnowledgeEntry(question_canonical=help_request.question.strip().lower(), answer=answer, source_help_request_id=help_request.id)
    session.add(kb)
    session.flush()
    return response


def mark_help_request_unresolved(session: Session, *, help_request: HelpRequest) -> HelpRequest:
    help_request.status = HelpRequestStatus.UNRESOLVED
    session.flush()
    return help_request


def get_pending_help_requests(session: Session) -> Iterable[HelpRequest]:
    return session.execute(select(HelpRequest).where(HelpRequest.status == HelpRequestStatus.PENDING).order_by(HelpRequest.created_at.asc())).scalars().all()


def get_help_request_by_id(session: Session, help_request_id: int) -> Optional[HelpRequest]:
    return session.get(HelpRequest, help_request_id)


