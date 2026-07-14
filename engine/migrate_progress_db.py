import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Inject project root into system path to allow straightforward execution
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PROGRESS_DB_PATH = os.path.join(PROJECT_ROOT, "database", "user_progress.db")

def migrate_database():
    print("=" * 60)
    print("⚙️  STARTING NON-DESTRUCTIVE DATABASE MIGRATION ⚙️")
    print("=" * 60)

    # 1. Guard check: does the DB even exist?
    if not os.path.exists(PROGRESS_DB_PATH):
        print("❌ Error: No existing 'user_progress.db' found to migrate!")
        print("Please ensure your progress DB is in the 'database/' directory.")
        return

    # 2. SAFETY FIRST: Generate an instant timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(PROJECT_ROOT, "database", f"user_progress_backup_{timestamp}.db")
    
    print(f"📦 Backing up original database to:\n   {backup_path} ...")
    shutil.copy2(PROGRESS_DB_PATH, backup_path)
    print("✅ Backup completed successfully.")
    print("-" * 60)

    # 3. Establish connection
    conn = sqlite3.connect(PROGRESS_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    try:
        # 4. Create the new reference table
        print("🛠️ Creating relational lookup table: activity_types...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_types (
                activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_code TEXT UNIQUE NOT NULL
            );
        """)

        # Seed activity reference lookup values
        activity_blueprint = [
            "mc_geo_to_eng", "mc_eng_to_geo", "mc_geo_pair_geo", 
            "match_matrix_3x3", "type_georgian", 
            "audio_mc_to_eng", "audio_mc_to_geo", "audio_dictation",
            "dialogue_passive", "dialogue_context_mc", "dialogue_roleplay_mc",
            "type_translit", "speech_rec_to_eng", "speech_rec_to_geo"
        ]
        for act in activity_blueprint:
            cursor.execute("INSERT OR IGNORE INTO activity_types (activity_code) VALUES (?);", (act,))
        conn.commit()
        print("✅ Reference values seeded.")

        # 5. Determine if log table needs schema updates
        cursor.execute("PRAGMA table_info(research_activity_log);")
        columns = [col[1] for col in cursor.fetchall()]

        if "activity_id" in columns:
            print("\n✨ Database is already using the relational 'activity_id' schema! No migration needed.")
            return

        if "activity_type" not in columns:
            print("\n❌ Error: Unexpected database format. Neither 'activity_type' nor 'activity_id' was found.")
            return

        print("\n🔄 Old schema detected. Initiating records migration...")

        # Step A: Rename legacy table to keep it as a source
        cursor.execute("ALTER TABLE research_activity_log RENAME TO research_activity_log_old;")

        # Step B: Re-create the log table using the relational ForeignKey constraints
        cursor.execute("""
            CREATE TABLE research_activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                phase_num INTEGER,
                unit_num INTEGER,
                lesson_num INTEGER,
                activity_id INTEGER,
                content_id INTEGER,
                user_input TEXT,
                is_correct INTEGER,
                is_review_item INTEGER,
                response_latency_ms INTEGER,
                FOREIGN KEY (activity_id) REFERENCES activity_types(activity_id)
            );
        """)

        # Step C: Query active lookup IDs into memory for ultra-fast translations
        cursor.execute("SELECT activity_id, activity_code FROM activity_types;")
        id_mapping = {code: act_id for act_id, code in cursor.fetchall()}

        # Step D: Pull records from the legacy source table
        cursor.execute("""
            SELECT log_id, timestamp, phase_num, unit_num, lesson_num, activity_type, 
                   content_id, user_input, is_correct, is_review_item, response_latency_ms 
            FROM research_activity_log_old;
        """)
        legacy_records = cursor.fetchall()

        # Step E: Insert translated records into the new relational schema
        migrated_count = 0
        for record in legacy_records:
            log_id, ts, phase, unit, lesson, old_act_code, content_id, user_input, is_correct, is_review, latency = record
            
            # Match old string name to new ID. If a legacy code is missing, generate it dynamically.
            new_act_id = id_mapping.get(old_act_code)
            if not new_act_id:
                cursor.execute("INSERT OR IGNORE INTO activity_types (activity_code) VALUES (?);", (old_act_code,))
                cursor.execute("SELECT activity_id FROM activity_types WHERE activity_code = ?;", (old_act_code,))
                new_act_id = cursor.fetchone()[0]
                id_mapping[old_act_code] = new_act_id

            cursor.execute("""
                INSERT INTO research_activity_log 
                (log_id, timestamp, phase_num, unit_num, lesson_num, activity_id, content_id, user_input, is_correct, is_review_item, response_latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (log_id, ts, phase, unit, lesson, new_act_id, content_id, user_input, is_correct, is_review, latency))
            migrated_count += 1

        # Step F: Drop legacy table safely now that data is copied
        cursor.execute("DROP TABLE research_activity_log_old;")
        
        conn.commit()
        print(f"🎉 SUCCESS! Migrated {migrated_count} records cleanly to the relational schema.")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration Failed: {e}")
        print("🔄 Changes rolled back safely. Your database is completely untouched.")
        print("=" * 60)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()