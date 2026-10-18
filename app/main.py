from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import uuid
import os
import shutil
from datetime import datetime, timezone, timedelta

from app.db import init_db, DB_PATH
from app.audit import append_event, verify_chain

app = FastAPI(title="SahayaNidhi Civic AI Governance", version="1.0.0")

# Enable CORS for live mobile and web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded evidence files publicly
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "platform": "IBM LinuxONE s390x"}

@app.get("/api/workers")
def get_workers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    workers = conn.execute("SELECT * FROM workers").fetchall()
    conn.close()
    return [dict(w) for w in workers]

# REAL-TIME CITIZEN SUBMISSION ENDPOINT
@app.post("/api/tokens")
async def create_realtime_token(
    description: str = Form(...),
    category: str = Form("other"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo: UploadFile = File(None)
):
    token_id = f"TKN-{uuid.uuid4().hex[:6].upper()}"
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Save live uploaded photo if present
    photo_path = None
    if photo:
        file_extension = os.path.splitext(photo.filename)[1] or ".jpg"
        file_name = f"{token_id}_before{file_extension}"
        photo_path = os.path.join("uploads", file_name)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

    # Dynamic SLA calculation (Default 24h, will be customized by Member 2's intake agent)
    deadline_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO incidents (incident_id, category, latitude, longitude, status, report_count) VALUES (?, ?, ?, ?, ?, ?)",
        (incident_id, category, latitude, longitude, "OPEN", 1)
    )
    cursor.execute(
        """
        INSERT INTO tokens (token_id, incident_id, description, category, severity_score, severity_level, sla_hours, status, deadline_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (token_id, incident_id, description, category, 0.75, "HIGH", 24, "NEW", deadline_at, created_at)
    )
    conn.commit()
    conn.close()
    
    # Log real-time event to SHA-256 audit chain
    append_event(
        token_id, 
        "TOKEN_CREATED", 
        {
            "description": description, 
            "category": category, 
            "latitude": latitude, 
            "longitude": longitude,
            "photo_path": photo_path,
            "created_at": created_at
        }
    )
    
    return {
        "success": True,
        "token_id": token_id, 
        "incident_id": incident_id, 
        "status": "NEW", 
        "sla_hours": 24,
        "photo_url": f"/uploads/{os.path.basename(photo_path)}" if photo_path else None
    }

# GET ALL LIVE TOKENS
@app.get("/api/tokens")
def get_all_tokens():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    tokens = conn.execute("SELECT * FROM tokens ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(t) for t in tokens]

@app.get("/api/audit/verify")
def verify_audit():
    return verify_chain()
