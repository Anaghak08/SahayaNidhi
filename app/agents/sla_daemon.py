import time
import sqlite3
from datetime import datetime

def _get_connection():
    """Connects to the SQLite database using the available helper in app.db."""
    import app.db as db_module
    if hasattr(db_module, "get_db_connection"):
        return db_module.get_db_connection()
    elif hasattr(db_module, "get_connection"):
        return db_module.get_connection()
    elif hasattr(db_module, "connect_db"):
        return db_module.connect_db()
    else:
        # Fallback direct connection
        return sqlite3.connect("data/civic.db")

def check_and_escalate_slas():
    """Queries active tickets and updates status to SLA_BREACHED if deadline passed."""
    conn = _get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        SELECT token_id, category, severity_level, deadline_at, status 
        FROM tokens 
        WHERE status IN ('NEW', 'ASSIGNED', 'IN_PROGRESS') 
        AND deadline_at IS NOT NULL 
        AND deadline_at < ?
    """, (now_str,))
    
    expired_tokens = cursor.fetchall()
    breached_count = 0
    
    for token in expired_tokens:
        token_id, category, severity, deadline, old_status = token
        
        cursor.execute("""
            UPDATE tokens 
            SET status = 'SLA_BREACHED' 
            WHERE token_id = ?
        """, (token_id,))
        
        try:
            from app.audit import append_audit_event
            append_audit_event(
                conn, 
                token_id=token_id, 
                event_type="SLA_BREACHED", 
                payload={"previous_status": old_status, "breached_at": now_str, "deadline": deadline}
            )
        except (ImportError, Exception):
            pass
            
        breached_count += 1
        print(f"[SLA DAEMON] Token {token_id} ({category}) BREACHED! Deadline was {deadline}")
        
    conn.commit()
    conn.close()
    return breached_count

def run_daemon_loop(poll_interval: int = 30):
    print(f"[SLA DAEMON] Started. Polling every {poll_interval} seconds...")
    try:
        while True:
            breached = check_and_escalate_slas()
            if breached > 0:
                print(f"[SLA DAEMON] Processed {breached} SLA breach(es).")
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("[SLA DAEMON] Shutting down daemon gracefully.")

if __name__ == "__main__":
    run_daemon_loop()
