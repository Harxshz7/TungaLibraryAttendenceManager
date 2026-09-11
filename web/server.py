import sqlite3
import json
import hashlib
import secrets
import asyncio
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

# --- Patch the Database Connection to be Read-Only ---
import models.database
_original_get_connection = models.database.get_connection

def ro_get_connection():
    db_uri = f"file:{models.database.DB_PATH}?mode=ro"
    return sqlite3.connect(db_uri, uri=True, timeout=30, isolation_level=None)

models.database.get_connection = ro_get_connection

from models.session_repo import get_live_sessions, get_student_history_range
from services.analytics_service import get_daily_averages, get_peak_hours, get_top_users, get_weekly_trends

app = FastAPI(title="Tunga Library Dashboard")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    config_path = models.database.DB_PATH.parent / "web_config.json"
    if not config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Web dashboard not configured.",
            headers={"WWW-Authenticate": "Basic"},
        )
        
    with open(config_path, "r") as f:
        config = json.load(f)
        
    correct_username = config.get("username", "")
    stored_hash = config.get("password_hash", "")
    
    candidate_hash = hashlib.sha256(credentials.password.encode('utf-8')).hexdigest()
    
    is_user_ok = secrets.compare_digest(credentials.username, correct_username)
    is_pass_ok = secrets.compare_digest(candidate_hash, stored_hash)
    
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def dashboard_home(request: Request, username: str = Depends(get_current_username)):
    sessions = get_live_sessions()
    return templates.TemplateResponse(request=request, name="index.html", context={"sessions": sessions})

@app.get("/events/live-sessions")
async def live_sessions_events(request: Request, username: str = Depends(get_current_username)):
    async def event_generator():
        last_signature = None
        while True:
            if await request.is_disconnected():
                break

            try:
                sessions = get_live_sessions()
                # Track structural changes: student_id, name, class, start_at, end_at, is_estimated
                signature = [(s[0], s[1], s[2], s[3], s[4], s[6]) for s in sessions]

                if signature != last_signature:
                    last_signature = signature
                    payload = [
                        {
                            "student_id": s[0],
                            "name": s[1],
                            "class": s[2],
                            "start_at": s[3],
                            "end_at": s[4] if s[4] else None,
                            "duration_sec": s[5],
                            "is_estimated": s[6]
                        }
                        for s in sessions
                    ]
                    yield f"data: {json.dumps(payload)}\n\n"
                else:
                    # Keep-alive ping comment
                    yield ": ping\n\n"
            except Exception:
                break

            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/history")
def history_view(request: Request, student_id: str = "", username: str = Depends(get_current_username)):
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    history = []
    if student_id:
        history = get_student_history_range(student_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
    return templates.TemplateResponse(request=request, name="history.html", context={
        "student_id": student_id,
        "history": history,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    })

@app.get("/analytics")
def analytics_view(request: Request, username: str = Depends(get_current_username)):
    avg_visits, avg_hours = get_daily_averages() or (0, 0)
    peak_hours = get_peak_hours()
    top_users = get_top_users()
    weekly_trends = get_weekly_trends()
    
    return templates.TemplateResponse(request=request, name="analytics.html", context={
        "avg_visits": avg_visits,
        "avg_hours": avg_hours,
        "peak_hours": peak_hours,
        "top_users": top_users,
        "weekly_trends": weekly_trends
    })

