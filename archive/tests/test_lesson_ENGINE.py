import random
from engine.lesson_engine import LessonSession

def run_terminal_lesson(session):
    print("=" * 60)
    print(f"🌟 STARTING REFINED TERMINAL PLAYTEST HARNESS 🌟")
    print(f"📍 Coordinates: Phase {session.phase_num} | Unit {session.unit_num} | Lesson {session.lesson_num}")
    print(f"Total Combined Multi-Activity Exercises: {session.total_exercises}")
    print("=" * 60)

    while True:
        card = session.get_next_exercise()
        if not card:
            print("\n🎉 VICTORY! All targeted activities cleared successfully!")
            break
            
        activity = card["activity"]
        target = card.get("target")
        targets = card.get("targets")
        
        print("\n" + "-"*40)
        is_correct = True
        
        # --- RECEPTIVE & RECOGNITION ACTIVITY DRIVERS ---
        if activity == "mc_geo_to_eng":
            print(f"📝 MULTIPLE CHOICE (Georgian Script -> English Selection)")
            print(f"Georgian Source Word:  \033[1;36m{target['geo']}\033[0m")
            options = [target["eng"]] + card["distractors"]
            random.shuffle(options)
            for i, opt in enumerate(options, 1): print(f"  [{i}] {opt}")
            ans = input("Your Choice (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["eng"])

        elif activity == "mc_eng_to_geo":
            print(f"📝 MULTIPLE CHOICE (English -> Georgian Script Selection)")
            print(f"English Source Meaning:  \033[1;33m{target['eng']}\033[0m")
            options = [target["geo"]] + card["distractors"]
            random.shuffle(options)
            for i, opt in enumerate(options, 1): print(f"  [{i}] {opt}")
            ans = input("Your Choice (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["geo"])

        elif activity == "mc_geo_pair_geo":
            print(f"🗣️  CONVERSATIONAL PAIRING (Contextual Response matching)")
            print(f"Prompt Question: \033[1;36m{target['prompt_geo']}\033[0m ({target['prompt_eng']})")
            options = [target["correct_geo"]] + card["distractors"]
            random.shuffle(options)
            for i, opt in enumerate(options, 1): print(f"  [{i}] {opt}")
            ans = input("Choose contextually matching response (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["correct_geo"])

        # --- PRODUCTION & BOARD MECHANICS DRIVERS ---
        elif activity == "match_matrix_3x3":
            print(f"🧩 MATCH MATRIX 3x3 (Grid Clearance Module)")
            geo_list = [t['geo'] for t in targets]
            eng_list = [t['eng'] for t in targets]
            random.shuffle(geo_list)
            random.shuffle(eng_list)
            print("  GEORGIAN KEYPAD           ENGLISH TARGETS")
            for i in range(3):
                print(f"  {i+1}. {geo_list[i]:<20} {i+4}. {eng_list[i]}")
            input("Press [ENTER] to validate and clear the board matrix...")
            is_correct = True

        elif activity == "type_georgian":
            print(f"⌨️ PRODUCTION CRITICAL (Native Characters Input)")
            print(f"Target Concept Translation: \033[1;33m{target['eng']}\033[0m")
            if target.get('trans'): print(f"Acoustic Prompt: {target['trans']}")
            ans = input("Type complete Georgian characters string: ").strip()
            is_correct = (ans.replace("!","").replace(".","") == target["geo"].replace("!","").replace(".",""))

        # --- AUDIO EXERCISE ENGINE SIMULATORS ---
        elif activity == "audio_mc_to_eng":
            print(f"🔊 LISTENING COMPREHENSION (Audio -> English Option)")
            print(f"[Acoustic Audio Playback Stream]: '{target['geo']}' Output Signal")
            options = [target["eng"]] + card["distractors"]
            random.shuffle(options)
            for i, opt in enumerate(options, 1): print(f"  [{i}] {opt}")
            ans = input("Select the translation you heard (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["eng"])

        elif activity == "audio_mc_to_geo":
            print(f"🔊 SCRIPTA RECOGNITION (Audio -> Script Match)")
            print(f"[Acoustic Audio Playback Stream]: '{target['geo']}' Output Signal")
            options = [target["geo"]] + card["distractors"]
            random.shuffle(options)
            for i, opt in enumerate(options, 1): print(f"  [{i}] {opt}")
            ans = input("Select characters matching the signal (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["geo"])

        elif activity == "audio_dictation":
            print(f"🔊 AUDIO DICTATION (Listen & Transcribe Production)")
            print(f"[Acoustic Audio Playback Stream]: '{target['geo']}' Output Signal")
            ans = input("Type native script expression heard: ").strip()
            is_correct = (ans.replace("!","").replace(".","") == target["geo"].replace("!","").replace(".",""))

        # --- ADVANCED CONTEXTUAL SPEECH MODULES ---
        elif activity == "dialogue_passive":
            print(f"💬 DIALOGUE PASSIVE RECONSTRUCTION: Code Reference [{target['code']}]")
            lines = session.get_dialogue_lines(target["id"])
            for speaker, geo, trans, eng in lines:
                display_trans = f" ({trans})" if trans else ""
                print(f"  Speaker {speaker}: {geo}{display_trans} -> {eng}")
            input("\nPress [ENTER] to move beyond conversation frame study elements...")
            is_correct = True

        elif activity == "dialogue_roleplay_mc":
            print(f"🎭 DIALOGUE ROLEPLAY CHALLENGE (Conversation Sequence Completion)")
            print(f"Speaker {target['speaker']} is expected to transition next.")
            print(f"Target Intent: User must express '{target['context_eng']}'")
            options = [target["correct_geo"]] + card["distractors"]
            random.shuffle(options)
            for i, opt in enumerate(options, 1): print(f"  [{i}] {opt}")
            ans = input(f"Choose what Speaker {target['speaker']} outputs (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["correct_geo"])

        elif activity == "dialogue_context_mc":
            print(f"🧠 STRUCTURAL CONTEXT COMPREHENSION CHECK")
            print(f"Extracted Narrative Block Quote: \033[1;36m\"{target['quote_geo']}\"\033[0m")
            options = [target["correct_eng"]] + card["distractors"]
            random.shuffle(options)
            for i, opt in enumerate(options, 1): print(f"  [{i}] {opt}")
            ans = input("Identify implied contextual definition (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["correct_eng"])

        res = session.submit_answer(is_correct)
        if activity not in ["dialogue_passive"]:
            if res["status"] == "correct":
                print("\033[1;32m✅ VALIDATION PASSED!\033[0m")
            else:
                print("\033[1;31m❌ MISMATCH DETECTED!\033[0m Card re-queued inside active buffer...")
        print(f"Active Session Deck Weight: {len(session.queue)} Modules Remaining | Completeness: {res['progress']*100:.1f}%")

if __name__ == "__main__":
    active_session = LessonSession()
    run_terminal_lesson(active_session)