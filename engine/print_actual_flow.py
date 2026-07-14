import os
import sys

# Inject project root into system path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.lesson_engine import LessonSession

def print_lesson_timeline(phase, unit, lesson):
    print("=" * 70)
    print(f"🎬 TIMELINE FLOW FOR PHASE {phase}, UNIT {unit}, LESSON {lesson} (REAL DATA) 🎬")
    print("=" * 70)

    # Initialize the session with your real databases
    session = LessonSession(
        db_name="content_poolbook.db",
        phase_num=phase,
        unit_num=unit,
        lesson_num=lesson
    )

    if not session.queue:
        print("⚠️ The generated queue is empty! Check your coordinates or database entries.")
        return

    print(f"📦 Total Cards Generated: {len(session.queue)}")
    print("-" * 70)

    # Walk through the queue card-by-card to see the flow structure
    for idx, card in enumerate(session.queue, 1):
        activity = card.get("activity")
        c_id = card.get("content_id")
        is_review = card.get("is_review_item", False)
        target = card.get("target", {})
        
        # Color coding formatting rules for clarity
        # Wave 1 (Recognition) = Cyan
        # Wave 2 (Audio) = Yellow
        # Wave 3 (Production) = Green
        # SRS Reviews = Magenta
        # Milestone Elements (Matrix/Dialogue) = Blue
        
        color_start = "\033[0m"
        category = "UNKNOWN"
        preview_text = ""

        if is_review:
            color_start = "\033[95m" # Magenta
            category = "⚠️ SRS REVIEW"
            preview_text = f"'{target.get('eng')}' -> Type in Georgian"
        elif activity in ["mc_geo_to_eng", "mc_eng_to_geo"]:
            color_start = "\033[96m" # Cyan
            category = "🌊 WAVE 1: RECOG"
            preview_text = f"'{target.get('geo')}' ⇋ '{target.get('eng')}'"
        elif activity in ["audio_mc_to_eng", "audio_mc_to_geo"]:
            color_start = "\033[93m" # Yellow
            category = "🎧 WAVE 2: AUDIO"
            preview_text = f"Listen ⇋ '{target.get('geo') or target.get('eng')}'"
        elif activity in ["type_georgian", "audio_dictation"]:
            color_start = "\033[92m" # Green
            category = "✍️ WAVE 3: PROD "
            preview_text = f"'{target.get('eng')}' -> Produce Georgian"
        elif activity == "mc_geo_pair_geo":
            color_start = "\033[94m" # Blue
            category = "💬 CONVO PAIR "
            preview_text = f"Prompt: '{target.get('prompt_geo')}'"
        elif activity == "match_matrix_3x3":
            color_start = "\033[34m" # Dark Blue
            category = "🧩 MATRIX GRID"
            targets_list = card.get("targets", [])
            preview_text = f"Match group of {len(targets_list)} words"
        elif activity.startswith("dialogue_"):
            color_start = "\033[35m" # Purple
            category = "📖 DIALOGUE   "
            preview_text = f"Mode: {activity} (ID: {c_id})"

        color_end = "\033[0m"

        print(f"[{idx:02d}] {color_start}[{category}]{color_end} "
              f"Activity: {activity:<22} | ID: {str(c_id):<8} | {preview_text}")

    print("=" * 70)

if __name__ == "__main__":
    # Run the timeline viewer for Phase 1, Unit 1, Lesson 1
    print_lesson_timeline(phase=1, unit=1, lesson=1)