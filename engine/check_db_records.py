import os
import sqlite3
import sys

# Get the absolute path to your real user_progress.db
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "database", "user_progress.db")

def check_records():
    print("=" * 60)
    print("🔍 PEEKING INTO REAL user_progress.db 🔍")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print("❌ Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Fetch the 5 most recent answers logged
        cursor.execute("""
            SELECT log_id, timestamp, activity_id, content_id, is_correct, user_input 
            FROM research_activity_log 
            ORDER BY log_id DESC 
            LIMIT 5;
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("📭 The activity log is currently empty.")
        else:
            print(f"✅ Found {len(records)} recent records. Here are the latest ones:\n")
            for r in records:
                log_id, ts, act_id, c_id, correct, user_input = r
                status = "✅ CORRECT" if correct else "❌ INCORRECT"
                input_str = f"| Input: '{user_input}'" if user_input else ""
                
                print(f"Log ID: {log_id:03d} | Time: {ts} | Activity ID: {act_id} | Content ID: {c_id:<4} | {status} {input_str}")
                
    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()
        print("=" * 60)

if __name__ == "__main__":
    check_records()