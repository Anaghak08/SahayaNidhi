from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta

from app.db import init_db, DB_PATH
from app.audit import append_event, verify_chain

app = FastAPI(title="SahayaNidhi Civic AI Governance", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/api/tokens")
def create_token(
    description: str = Form(...),
    category: str = Form("other"),
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    token_id = f"TKN-{uuid.uuid4().hex[:6].upper()}"
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    deadline_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO incidents (incident_id, category, latitude, longitude, status, report_count) VALUES (?, ?, ?, ?, ?, ?)",
        (incident_id, category, latitude, longitude, "OPEN", 1)
    )
    cursor.execute(
        "INSERT INTO tokens (token_id, incident_id, description, category, severity_score, severity_level, sla_hours, status, deadline_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (token_id, incident_id, description, category, 0.75, "HIGH", 24, "NEW", deadline_at, created_at)
    )
    conn.commit()
    conn.close()
    
    append_event(token_id, "TOKEN_CREATED", {"description": description, "category": category, "latitude": latitude, "longitude": longitude})
    return {"token_id": token_id, "incident_id": incident_id, "status": "NEW", "sla_hours": 24}

@app.post("/api/tokens/{token_id}/assign")
def assign_worker(token_id: str, worker_id: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tokens SET assigned_worker_id = ?, status = 'ASSIGNED' WHERE token_id = ?", (worker_id, token_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Token not found")
    conn.commit()
    conn.close()
    
    append_event(token_id, "WORKER_ASSIGNED", {"worker_id": worker_id})
    return {"token_id": token_id, "assigned_worker_id": worker_id, "status": "ASSIGNED"}

@app.get("/api/audit/verify")
def verify_audit():
    return verify_chain()
