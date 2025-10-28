import asyncio
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
import logging
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from db import get_session
from db.repository import (
    init_db,
    get_pending_help_requests,
    get_help_request_by_id,
    resolve_help_request,
    mark_help_request_unresolved,
)
from db.models import HelpRequestStatus, KnowledgeEntry


app = FastAPI(title="Supervisor Console")
templates = Jinja2Templates(directory="web/templates")
_sweeper_task = None


@app.on_event("startup")
async def on_startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with get_session() as session:
        pending = get_pending_help_requests(session)
    return templates.TemplateResponse("home.html", {"request": request, "pending": pending})


@app.get("/requests", response_class=HTMLResponse)
async def list_requests(request: Request):
    with get_session() as session:
        pending = get_pending_help_requests(session)
    return templates.TemplateResponse("requests.html", {"request": request, "pending": pending})


@app.get("/requests/{request_id}", response_class=HTMLResponse)
async def view_request(request: Request, request_id: int):
    with get_session() as session:
        hr = get_help_request_by_id(session, request_id)
        if not hr:
            raise HTTPException(status_code=404, detail="Request not found")
    return templates.TemplateResponse("request_detail.html", {"request": request, "hr": hr})


@app.post("/requests/{request_id}/resolve")
async def resolve_request(request_id: int, answer: str = Form(...), supervisor_id: Optional[str] = Form(None)):
    with get_session() as session:
        hr = get_help_request_by_id(session, request_id)
        if not hr:
            raise HTTPException(status_code=404, detail="Request not found")
        if hr.status != HelpRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request already finalized")
        resolve_help_request(session, help_request=hr, answer=answer, supervisor_id=supervisor_id)
        # Simulate immediate text/callback to original caller via log
        room_name = hr.call_session.room_name if hr.call_session else "unknown_room"
        logging.getLogger("supervisor-console").info(
            f"[CALLER FOLLOW-UP] Room {room_name} — replying to original caller with: {answer}"
        )
    return RedirectResponse(url=f"/requests/{request_id}", status_code=303)


@app.post("/requests/{request_id}/unresolved")
async def mark_unresolved(request_id: int):
    with get_session() as session:
        hr = get_help_request_by_id(session, request_id)
        if not hr:
            raise HTTPException(status_code=404, detail="Request not found")
        mark_help_request_unresolved(session, help_request=hr)
    return RedirectResponse(url=f"/requests/{request_id}", status_code=303)


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    from sqlalchemy import select
    from db.models import HelpRequest
    with get_session() as session:
        items = session.execute(
            select(HelpRequest).where(HelpRequest.status != HelpRequestStatus.PENDING).order_by(HelpRequest.updated_at.desc())
        ).scalars().all()
    return templates.TemplateResponse("history.html", {"request": request, "items": items})


@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge(request: Request):
    from sqlalchemy import select
    with get_session() as session:
        items = session.execute(select(KnowledgeEntry).order_by(KnowledgeEntry.created_at.desc())).scalars().all()
    return templates.TemplateResponse("knowledge.html", {"request": request, "items": items})


# Simple background task to mark timeouts as unresolved
async def timeout_sweeper_loop():
    from sqlalchemy import select
    from db.models import HelpRequest
    try:
        while True:
            now = datetime.utcnow()
            with get_session() as session:
                expiring = session.execute(
                    select(HelpRequest).where(
                        HelpRequest.status == HelpRequestStatus.PENDING,
                        HelpRequest.timeout_at != None,  # noqa: E711
                        HelpRequest.timeout_at <= now,
                    )
                ).scalars().all()
                for hr in expiring:
                    mark_help_request_unresolved(session, help_request=hr)
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        # graceful shutdown
        return


@app.on_event("startup")
async def start_timeout_sweeper():
    global _sweeper_task
    _sweeper_task = asyncio.create_task(timeout_sweeper_loop())


@app.on_event("shutdown")
async def stop_timeout_sweeper():
    global _sweeper_task
    if _sweeper_task is not None:
        _sweeper_task.cancel()
        try:
            await _sweeper_task
        except asyncio.CancelledError:
            pass
        _sweeper_task = None


