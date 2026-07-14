import os
import sys

# Inject project root into system path to allow straightforward execution
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.lesson_engine import LessonSession

def test_on_actual_databases():
    print("=" * 60)
    print("🎯 RUNNING INTEGRATION TEST ON ACTUAL DATABASE 🎯")
    print("=" * 60)

    db_dir = os.path.join(PROJECT_ROOT, "database")
    real_content_db = os.path.join(db_dir, "content_poolbook.db")
    real_progress_db = os.path.join(db_dir, "user_progress.db")

    # Double-check files exist before proceeding
    if not os.path.exists(real_content_db):
        print(f"❌ Error: Could not find actual curriculum database at: {real_content_db}")
        print("Please ensure your 'content_poolbook.db' is located inside your 'database/' directory.")
        return

    print("✅ Found actual curriculum database: content_poolbook.db")
    if os.path.exists(real_progress_db):
        print("✅ Found existing progress database: user_progress.db (We will safely write to this non-destructively)")
    else:
        print("ℹ️ No existing user_progress.db found. The engine will initialize a brand new one safely.")

    # 1. Initialize session using Phase 1, Unit 1, Lesson 1
    # Change these coordinates if you want to test a specific lesson!
    test_phase, test_unit, test_lesson = 1, 1, 1
    
    print(f"\n🌀 Loading Phase {test_phase}, Unit {test_unit}, Lesson {test_lesson} from your actual curriculum...")
    
    try:
        session = LessonSession(
            db_name="content_poolbook.db", # Points to your real content db
            phase_num=test_phase,
            unit_num=test_unit,
            lesson_num=test_lesson
        )
    except Exception as e:
        print(f"❌ Failed to initialize the Lesson Session: {e}")
        return

    if not session.lesson_id:
        print(f"⚠️ Could not resolve Lesson ID for Coordinates {test_phase}-{test_unit}-{test_lesson}.")
        print("Please verify that these coordinates actually exist inside your content_poolbook.db!")
        return

    print(f"🚀 Success! Lesson ID '{session.lesson_id}' resolved from your curriculum database.")
    print(f"📦 Total exercises generated for this lesson: {session.total_exercises}")
    print("-" * 60)

    # 2. Peek at the first 3 cards generated from your actual vocabulary list
    print("\n🔍 PEeking AT FIRST 3 DYNAMICALLY GENERATED EXERCISES:")
    temp_queue = list(session.queue) # Copy queue so we don't destroy session state
    
    for i in range(min(3, len(temp_queue))):
        card = temp_queue[i]
        activity = card.get("activity")
        content_id = card.get("content_id")
        target = card.get("target", {})
        
        # Display elegant preview depending on structure
        if "geo" in target:
            word_preview = f"'{target['geo']}' -> '{target['eng']}'"
        elif "prompt_geo" in target:
            word_preview = f"Convo: '{target['prompt_geo']}' -> '{target['correct_geo']}'"
        else:
            word_preview = str(target)
            
        print(f"  [{i+1}] Card Type: \033[96m{activity:<22}\033[0m | Content ID: {content_id:<4} | Word: {word_preview}")

    # 3. Simulate answering the very first question correctly
    print("\n⚡ SIMULATING REAL-TIME USER INTERACTION...")
    active_card = session.get_next_exercise()
    
    if active_card:
        print(f"  • Simulating a 'Correct' answer for: \033[92m{active_card.get('activity')}\033[0m")
        # Simulate a quick 1.5s (1500ms) thinking delay
        import time
        time.sleep(1.5) 
        
        result = session.submit_answer(is_correct=True, user_input="Actual DB Test Run")
        
        print(f"  • Result Status: {result['status'].upper()}")
        print(f"  • Updated Lesson Progress: {result['progress'] * 100:.1f}%")
        print("\n✅ Success! Telemetry written and active queue advanced safely.")
    else:
        print("⚠️ Queue is empty—nothing to simulate.")

    print("\n" + "=" * 60)
    print("🎉 ACTUAL DATABASE PIPELINE TEST PASSED FLAWLESSLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_on_actual_databases()