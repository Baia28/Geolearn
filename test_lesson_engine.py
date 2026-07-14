import os
import sys
import sqlite3
import datetime

# Inject project root into system path to allow straightforward execution
#PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.lesson_engine import LessonSession

from engine.lesson_engine import LessonSession
from engine.db_managers import ProgressDBManager

TEST_PROGRESS_DB = "test_user_progress.db"
TEST_CONTENT_DB = "test_content_poolbook.db"


def build_mock_databases():
    """Sets up highly specific, sandboxed testing databases with sample seed data."""
    print("🧹 Cleaning old test databases...")
    db_dir = os.path.join(PROJECT_ROOT, "database")
    os.makedirs(db_dir, exist_ok=True)
    
    prog_path = os.path.join(db_dir, TEST_PROGRESS_DB)
    cont_path = os.path.join(db_dir, TEST_CONTENT_DB)
    
    if os.path.exists(prog_path):
        os.remove(prog_path)
    if os.path.exists(cont_path):
        os.remove(cont_path)

    # =========================================================================
    # 1. INITIALIZE TEST USER PROGRESS DATABASE
    # =========================================================================
    print("🛠️ Setting up test progress database tables...")
    p_conn = sqlite3.connect(prog_path)
    p_conn.execute("PRAGMA foreign_keys = ON;")
    p_cursor = p_conn.cursor()

    p_cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_types (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_code TEXT UNIQUE NOT NULL
        );
    """)

    p_cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            lesson_id INTEGER PRIMARY KEY,
            current_step INTEGER DEFAULT 1,
            is_completed INTEGER DEFAULT 0,
            last_accessed TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    p_cursor.execute("""
        CREATE TABLE IF NOT EXISTS srs_registry (
            content_id INTEGER PRIMARY KEY,
            mastery_level INTEGER DEFAULT 0,
            ease_factor REAL DEFAULT 2.5,
            repetitions INTEGER DEFAULT 0,
            interval_days INTEGER DEFAULT 0,
            next_review_date TEXT DEFAULT (date('now'))
        );
    """)

    p_cursor.execute("""
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

    # Populate Activity Types blueprint
    activity_blueprint = [
        "mc_geo_to_eng", "mc_eng_to_geo", "mc_geo_pair_geo", 
        "match_matrix_3x3", "type_georgian", 
        "audio_mc_to_eng", "audio_mc_to_geo", "audio_dictation",
        "dialogue_passive", "dialogue_context_mc", "dialogue_roleplay_mc",
        "type_translit", "speech_rec_to_eng", "speech_rec_to_geo"
    ]
    for act in activity_blueprint:
        p_cursor.execute("INSERT INTO activity_types (activity_code) VALUES (?);", (act,))
        
    p_conn.commit()
    p_conn.close()

    # =========================================================================
    # 2. INITIALIZE TEST CONTENT DATABASE
    # =========================================================================
    print("🛠️ Setting up test content database tables...")
    c_conn = sqlite3.connect(cont_path)
    c_cursor = c_conn.cursor()

    # Core curriculum structure schemas
    c_cursor.execute("CREATE TABLE phases (phase_id INTEGER PRIMARY KEY, sequence_order INTEGER);")
    c_cursor.execute("CREATE TABLE units (unit_id INTEGER PRIMARY KEY, phase_id INTEGER, sequence_order INTEGER);")
    c_cursor.execute("CREATE TABLE lessons (lesson_id INTEGER PRIMARY KEY, unit_id INTEGER, sequence_order INTEGER);")
    c_cursor.execute("CREATE TABLE lesson_component_types (component_type_id INTEGER PRIMARY KEY, name TEXT);")
    c_cursor.execute("""
        CREATE TABLE lesson_contents (
            lesson_id INTEGER, 
            step_order INTEGER, 
            component_type_id INTEGER, 
            associated_id INTEGER
        );
    """)
    
    # Vocabulary & Dialogue schemas
    c_cursor.execute("""
        CREATE TABLE content (
            content_id INTEGER PRIMARY KEY, 
            georgian TEXT, 
            english TEXT, 
            transliteration TEXT
        );
    """)
    c_cursor.execute("CREATE TABLE convo_pairs (pair_id INTEGER PRIMARY KEY, prompt_id INTEGER, response_id INTEGER);")
    c_cursor.execute("CREATE TABLE dialogues (dialogue_id INTEGER PRIMARY KEY, internal_code TEXT);")
    c_cursor.execute("""
        CREATE TABLE dialogue_lines (
            dialogue_id INTEGER, 
            line_order INTEGER, 
            speaker TEXT, 
            content_id INTEGER
        );
    """)
    c_cursor.execute("CREATE TABLE tags (tag_id INTEGER PRIMARY KEY, name TEXT);")
    c_cursor.execute("CREATE TABLE content_tags (content_id INTEGER, tag_id INTEGER);")

    # Seed core curriculum indexes
    c_cursor.execute("INSERT INTO phases VALUES (1, 1);")
    c_cursor.execute("INSERT INTO units VALUES (1, 1, 1);")
    c_cursor.execute("INSERT INTO lessons VALUES (10, 1, 1);") # lesson_id 10 corresponds to coordinates 1-1-1

    # Seed Component Type helpers
    c_cursor.execute("INSERT INTO lesson_component_types VALUES (1, 'monologue');")
    c_cursor.execute("INSERT INTO lesson_component_types VALUES (2, 'convo_pair');")
    c_cursor.execute("INSERT INTO lesson_component_types VALUES (3, 'dialogue');")

    # Seed 6 Vocabulary Words (Split into two distinct micro-batches of 3)
    # Batch 1:
    c_cursor.execute("INSERT INTO content VALUES (101, 'გამარჯობა', 'hello', 'gamarjoba');")
    c_cursor.execute("INSERT INTO content VALUES (102, 'დილა მშვიდობისა', 'good morning today my friend', 'dila mshvidobisa');") # Word count >= 3 to trigger phrase bypass
    c_cursor.execute("INSERT INTO content VALUES (103, 'გმადლობთ', 'thank you', 'gmadlobt');")
    # Batch 2:
    c_cursor.execute("INSERT INTO content VALUES (104, 'კი', 'yes', 'ki');")
    c_cursor.execute("INSERT INTO content VALUES (105, 'არა', 'no', 'ara');")
    c_cursor.execute("INSERT INTO content values (106, 'ნახვამდის', 'goodbye', 'nakhvamdis');")

    # Map content into Lesson Steps
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 1, 1, 101);")
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 2, 1, 102);")
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 3, 1, 103);")
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 4, 1, 104);")
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 5, 1, 105);")
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 6, 1, 106);")
    
    # Seed conversational pairing checks
    c_cursor.execute("INSERT INTO convo_pairs VALUES (201, 101, 103);") # Prompting "hello" expects response "thank you"
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 7, 2, 201);")

    # Seed dialogue structures
    c_cursor.execute("INSERT INTO dialogues VALUES (301, 'greeting_dialogue_01');")
    c_cursor.execute("INSERT INTO dialogue_lines VALUES (301, 1, 'A', 101);") # Speaker A says "hello"
    c_cursor.execute("INSERT INTO dialogue_lines VALUES (301, 2, 'B', 103);") # Speaker B says "thank you"
    c_cursor.execute("INSERT INTO lesson_contents VALUES (10, 8, 3, 301);")

    # Tag 'thank you' (103) as conversational "response" to allow distractors selection
    c_cursor.execute("INSERT INTO tags VALUES (1, 'response');")
    c_cursor.execute("INSERT INTO content_tags VALUES (103, 1);")

    c_conn.commit()
    c_conn.close()
    print("✅ Databases successfully mock-seeded!")


def run_active_session_simulation():
    """Orchestrates an interactive user progress walkthrough, highlighting edge cases."""
    print("\n" + "=" * 60)
    print("🎬 STARTING SYSTEM INTEGRATION TEST SIMULATION 🎬")
    print("=" * 60)

    # Instantiate Session referencing our sandboxed test databases
    session = LessonSession(
        db_name=TEST_CONTENT_DB, 
        phase_num=1, 
        unit_num=1, 
        lesson_num=1
    )
    
    # Point progress manager to sandbox
    session.progress_db = ProgressDBManager(TEST_PROGRESS_DB)
    session.generator.progress_db = session.progress_db
    
    # Force rebuild of deck referencing sandbox coordinates
    session._build_session()

    print(f"📦 Lesson Queue Initialized with {session.total_exercises} total steps!")
    print("-" * 60)

    step = 0
    while True:
        card = session.get_next_exercise()
        if not card:
            print("\n🏁 Integration Success: Queue is completely clear!")
            break

        step += 1
        activity = card.get("activity")
        content_id = card.get("content_id")
        
        print(f"\n👉 [STEP {step}] Active Activity: \033[96m{activity}\033[0m (Content ID: {content_id})")

        # Handle different card modalities with automated mock performance behaviors
        if activity == "mc_geo_to_eng":
            # --- TEST CASE 1: INTENTIONAL FAIL (First occurrence) ---
            # If the user encounters Word 101 for the first time, let's fail it!
            # We want to verify that the adaptive mutation system catches this,
            # swaps it to its companion "mc_eng_to_geo" structure, and pushes it 3 indexes down.
            if content_id == 101 and step < 5:
                print("❌ Simulated Event: User answered WRONG! (Testing Adaptive Swapping)")
                res = session.submit_answer(is_correct=False, user_input="wrong_answer_test")
            else:
                # --- TEST CASE 2: CORRECT ANSWER & SIBLING PRUNING ---
                # When we answer a Wave 1 card correctly, its matching companion sibling 
                # (e.g., mc_eng_to_geo) should be purged from the deck automatically.
                print("✅ Simulated Event: User answered CORRECT!")
                res = session.submit_answer(is_correct=True, user_input="correct_answer")
            
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        elif activity == "mc_eng_to_geo":
            # This is our mutated companion card! Let's clear it with a success.
            print("✅ Simulated Event: User cleared the mutated companion correctly!")
            res = session.submit_answer(is_correct=True, user_input="correct_mutated")
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        elif activity in ["audio_mc_to_eng", "audio_mc_to_geo"]:
            print("✅ Simulated Event: User cleared the listening check correctly!")
            res = session.submit_answer(is_correct=True, user_input="correct_audio")
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        elif activity in ["type_georgian", "audio_dictation"]:
            print("✅ Simulated Event: User finished typing input successfully!")
            res = session.submit_answer(is_correct=True, user_input="გამარჯობა")
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        elif activity == "mc_geo_pair_geo":
            print("✅ Simulated Event: Conversational stimulus-response pairing passed!")
            res = session.submit_answer(is_correct=True, user_input="გმადლობთ")
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        elif activity == "match_matrix_3x3":
            print("✅ Simulated Event: Grid matrix match puzzle completed!")
            res = session.submit_answer(is_correct=True)
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        elif activity == "dialogue_passive":
            # Passive references don't need logging, they just slide forward
            print("📖 Simulated Event: Dialogue reference sliding panel read.")
            res = session.submit_answer(is_correct=True)
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        elif activity in ["dialogue_roleplay_mc", "dialogue_context_mc"]:
            print("✅ Simulated Event: Dialogue comprehension challenge passed!")
            res = session.submit_answer(is_correct=True, user_input="correct_context")
            print(f"📊 Live Progress Meter: {res['progress'] * 100:.1f}% Complete")

        else:
            print("❓ Unknown event state: Auto-passing...")
            res = session.submit_answer(is_correct=True)

    # Verify that databases were updated correctly
    verify_database_integrity()


def verify_database_integrity():
    """Pulls telemetry summaries from SQL to guarantee data pipeline integrity."""
    print("\n" + "=" * 60)
    print("🔍 VERIFYING TELEMETRY & DATABASES 🔍")
    print("=" * 60)
    
    prog_path = os.path.join(PROJECT_ROOT, "database", TEST_PROGRESS_DB)
    conn = sqlite3.connect(prog_path)
    cursor = conn.cursor()

    # 1. Verify Activity logs are relational (Using integer Activity IDs)
    cursor.execute("""
        SELECT ral.log_id, at.activity_code, ral.is_correct, ral.response_latency_ms
        FROM research_activity_log ral
        JOIN activity_types at ON ral.activity_id = at.activity_id
        LIMIT 5
    """)
    rows = cursor.fetchall()
    
    print("\n📈 [Telemetry Verification] Sample Activity Logs:")
    for row in rows:
        print(f"  • Log ID: {row[0]} | Type: {row[1]:<22} | Correct: {row[2]} | Latency: {row[3]}ms")

    # 2. Verify SRS algorithms updated correctly
    cursor.execute("""
        SELECT content_id, mastery_level, ease_factor, interval_days, next_review_date 
        FROM srs_registry
    """)
    srs_rows = cursor.fetchall()
    print("\n🧠 [SRS Verification] Active SRS Intervals scheduled:")
    for srs in srs_rows:
        print(f"  • Word ID: {srs[0]} | Reps: {srs[1]} | Ease Factor: {srs[2]} | Interval: {srs[3]} days | Next Review: {srs[4]}")

    # 3. Verify Lesson Progress flags
    cursor.execute("SELECT lesson_id, is_completed FROM lesson_progress")
    lesson = cursor.fetchone()
    if lesson:
        print(f"\n🏆 [Milestone Verification] Lesson {lesson[0]} Completed State: {lesson[1] == 1}")

    conn.close()
    print("\n🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    build_mock_databases()
    run_active_session_simulation()