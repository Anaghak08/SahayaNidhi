import time
import sqlite3
from datetime import datetime

def run_once(db_path="data/civic.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query overdue active tokens
    cursor.execute("""
        SELECT token_id FROM tokens 
        WHERE status IN ('NEW', 'ASSIGNED', 'IN_PROGRESS') 
        AND deadline_at < CURRENT_TIMESTAMP
    """)
    overdue = cursor.fetchall()
    
    for (token_id,) in overdue:
        cursor.execute("UPDATE tokens SET status = 'SLA_BREACHED' WHERE token_id = ?", (token_id,))
        print(f"[SLA DAEMON] Token {token_id} marked as SLA_BREACHED")
        
    conn.commit()
    conn.close()
    return len(overdue)

if __name__ == "__main__":
    print("[SLA DAEMON] Checking for SLA breaches...")
    breaches = run_once()
    print(f"[SLA DAEMON] Processed {breaches} breach(es).")
