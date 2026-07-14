import sqlite3
import os

PROGRESS_DB_NAME = "database/user_progress.db"

def initialize_user_progress_system():
    print("=" * 60)
    print("🚀 INITIALIZING USER PROGRESS & RESEARCH DATABASE 🚀")
    print("=" * 60)
    
    # Force a fresh start if you want to wipe testing data (Optional)
    if os.path.exists(PROGRESS_DB_NAME):
       os.remove(PROGRESS_DB_NAME)

    conn = sqlite3.connect(PROGRESS_DB_NAME)
    cursor = conn.cursor()

    # 0. NEW: ACTIVITY TYPES REFERENCE TABLE
    print("🛠️ Creating table: activity_types...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_types (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_code TEXT UNIQUE NOT NULL
        );
    """)

    # Pre-populate the activity types from your blueprint
    activity_blueprint = [
        "mc_geo_to_eng", "mc_eng_to_geo", "mc_geo_pair_geo", 
        "match_matrix_3x3", "type_georgian", 
        "audio_mc_to_eng", "audio_mc_to_geo", "audio_dictation",
        "dialogue_passive", "dialogue_context_mc", "dialogue_roleplay_mc",
        "type_translit", "speech_rec_to_eng", "speech_rec_to_geo"
    ]

    for activity in activity_blueprint:
        cursor.execute(
            "INSERT OR IGNORE INTO activity_types (activity_code) VALUES (?);", 
            (activity,)
        )


    # 1. LESSON PROGRESS CHECKPOINTS (For Save / Resume / Restart feature)
    print("🛠️ Creating table: lesson_progress...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            lesson_id INTEGER PRIMARY KEY,
            current_step INTEGER DEFAULT 1,
            is_completed INTEGER DEFAULT 0,
            last_accessed TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. GLOBAL SRS REGISTRY (For long-term tracking and smart review injection)
    print("🛠️ Creating table: srs_registry...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS srs_registry (
            content_id INTEGER PRIMARY KEY,
            mastery_level INTEGER DEFAULT 0,
            ease_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            interval_days INTEGER DEFAULT 0,
            next_review_date TEXT DEFAULT (date('now'))
        );
    """)

    # 3. RESEARCH ACTIVITY LOG (Your granular, timestamped data goldmine)
    print("🛠️ Creating table: research_activity_log...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_activity_log (
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

    conn.commit()
    conn.close()
    print("\n✅ SUCCESS: 'user_progress.db' is fully deployed and ready for data tracking!")
    print("=" * 60)

if __name__ == "__main__":
    initialize_user_progress_system()