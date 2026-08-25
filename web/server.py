import sqlite3
import json
import hashlib
import secrets
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

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
    return templates.TemplateResponse("index.html", {"request": request, "sessions": sessions})

@app.get("/history")
def history_view(request: Request, student_id: str = "", username: str = Depends(get_current_username)):
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    history = []
    if student_id:
        history = get_student_history_range(student_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
    return templates.TemplateResponse("history.html", {
        "request": request, 
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
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "avg_visits": avg_visits,
        "avg_hours": avg_hours,
        "peak_hours": peak_hours,
        "top_users": top_users,
        "weekly_trends": weekly_trends
    })
