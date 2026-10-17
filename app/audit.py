import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any

DB_PATH = "data/civic.db"

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def compute_hash(previous_hash: str, token_id: str, event_type: str, created_at: str, event_json: str) -> str:
    """Computes SHA-256 hash for an audit record to ensure tamper resistance."""
    payload = f"{previous_hash}|{token_id}|{event_type}|{created_at}|{event_json}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def append_event(token_id: str, event_type: str, payload_data: Dict[str, Any]) -> str:
    """Appends an event to the audit_events table linked to the previous record's hash."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    previous_hash = last_row["event_hash"] if last_row else "GENESIS_HASH"
    
    created_at = datetime.now(timezone.utc).isoformat()
    event_json = json.dumps(payload_data, sort_keys=True)
    event_hash = compute_hash(previous_hash, token_id, event_type, created_at, event_json)
    
    cursor.execute(
        """
        INSERT INTO audit_events (token_id, event_type, event_json, previous_hash, event_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (token_id, event_type, event_json, previous_hash, event_hash, created_at)
    )
    conn.commit()
    conn.close()
    return event_hash

def verify_chain() -> Dict[str, Any]:
    """Recalculates every event's hash from the genesis block to detect database tampering."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_events ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    expected_previous = "GENESIS_HASH"
    for row in rows:
        if row["previous_hash"] != expected_previous:
            return {"valid": False, "corrupted_id": row["id"], "reason": "Previous hash link mismatch"}
            
        calculated = compute_hash(
            row["previous_hash"], 
            row["token_id"], 
            row["event_type"], 
            row["created_at"], 
            row["event_json"]
        )
        if calculated != row["event_hash"]:
            return {"valid": False, "corrupted_id": row["id"], "reason": "Hash tampering detected"}
            
        expected_previous = row["event_hash"]
        
    return {"valid": True, "total_events": len(rows)}
