import sqlite3
import os

DB_PATH = "data/civic.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id TEXT PRIMARY KEY,
        category TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT,
        report_count INTEGER DEFAULT 1
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        token_id TEXT PRIMARY KEY,
        incident_id TEXT,
        description TEXT,
        category TEXT,
        severity_score REAL,
        severity_level TEXT,
        sla_hours INTEGER,
        status TEXT,
        assigned_worker_id TEXT,
        deadline_at TEXT,
        created_at TEXT
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workers (
        worker_id TEXT PRIMARY KEY,
        name TEXT,
        zone TEXT
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id TEXT,
        event_type TEXT,
        event_json TEXT,
        previous_hash TEXT,
        event_hash TEXT,
        created_at TEXT
    )""")
    
    cursor.execute("SELECT COUNT(*) FROM workers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO workers (worker_id, name, zone) VALUES (?, ?, ?)",
            [
                ("W-101", "Asha Kumar", "Central"),
                ("W-102", "Ravi Shetty", "East"),
                ("W-103", "Meera Rao", "West")
            ]
        )
    conn.commit()
    conn.close()
