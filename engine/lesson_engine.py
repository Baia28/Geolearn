import sqlite3
import random

class LessonSession:
    #  Update __init__ to take Phase, Unit, and Lesson sequence numbers
    def __init__(self, db_path, phase_num, unit_num, lesson_num):
        self.db_path = db_path
        self.phase_num = phase_num
        self.unit_num = unit_num
        self.lesson_num = lesson_num
        
        # Game State
        self.queue = []            
        self.total_exercises = 0   
        self.completed_count = 0
        
        # Initialize the deck
        self._build_session()

    # ==========================================
    # 1. DATABASE FETCHING & DISTRACTORS
    # ====================================

    def _fetch_lesson_contents(self):
        """Grabs all monologues and dialogues using clean human curriculum numbers."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Step 1: Find the exact internal lesson_id using our sequence orders
        cursor.execute("""
            SELECT l.lesson_id 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            WHERE p.sequence_order = ? AND u.sequence_order = ? AND l.sequence_order = ?
        """, (self.phase_num, self.unit_num, self.lesson_num))
        
        res = cursor.fetchone()
        if not res:
            conn.close()
            return [], [] # Return empty if coordinates don't exist
            
        resolved_lesson_id = res[0]

        # 2. Step 2: Fetch Monologues using the resolved internal ID
        cursor.execute("""
            SELECT c.content_id, c.georgian, c.english, c.transliteration 
            FROM lesson_contents lc
            JOIN lesson_component_types lct ON lc.component_type_id = lct.component_type_id
            JOIN content c ON lc.associated_id = c.content_id
            WHERE lc.lesson_id = ? AND lct.name = 'monologue'
        """, (resolved_lesson_id,))
        monologues = cursor.fetchall()

        # 3. Step 3: Fetch Dialogues
        cursor.execute("""
            SELECT d.dialogue_id, d.internal_code 
            FROM lesson_contents lc
            JOIN lesson_component_types lct ON lc.component_type_id = lct.component_type_id
            JOIN dialogues d ON lc.associated_id = d.dialogue_id
            WHERE lc.lesson_id = ? AND lct.name = 'dialogue'
        """, (resolved_lesson_id,))
        dialogues = cursor.fetchall()
        
        conn.close()
        return monologues, dialogues

    def _get_distractors(self, content_id, limit=2):
        """
        Smart distractor generator. Pulls random wrong answers from the 
        master content table, excluding the correct answer.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT english, georgian 
            FROM content 
            WHERE content_id != ? 
            ORDER BY RANDOM() 
            LIMIT ?
        """, (content_id, limit))
        distractors = cursor.fetchall()
        
        conn.close()
        return distractors
    def get_dialogue_lines(self, dialogue_id):
        """Fetches the full script lines using your clean relational IDs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 🌟 Cleaned up to map dl.content_id directly to c.content_id ordered by line_order
        cursor.execute("""
            SELECT dl.speaker, c.georgian, c.transliteration, c.english 
            FROM dialogue_lines dl
            JOIN content c ON dl.content_id = c.content_id
            WHERE dl.dialogue_id = ? 
            ORDER BY dl.line_order ASC
        """, (dialogue_id,))
        lines = cursor.fetchall()
        
        conn.close()
        return lines


    # ==========================================
    # 2. THE PLAYLIST GENERATION TEMPLATE
    # ====================================
    def _build_session(self):
        """Translates raw database rows into an interactive queue of exercises."""
        monologues, dialogues = self._fetch_lesson_contents()
        
        if not monologues and not dialogues:
            print(f"[!] Warning: No content found linked to Lesson ID {self.lesson_id}")
            return

        # Phase 1: Receptive Recognition (Discovery / Fail Forward)
        for m in monologues:
            word_data = {"id": m[0], "geo": m[1], "eng": m[2], "trans": m[3]}
            distractors = self._get_distractors(word_data["id"], limit=2)
            
            self.queue.append({
                "activity": "mc_geo_to_eng",
                "target": word_data,
                "distractors": [d[0] for d in distractors] # English strings
            })

        # Phase 2: Auditory Integration 
        for m in monologues:
            word_data = {"id": m[0], "geo": m[1], "eng": m[2], "trans": m[3]}
            distractors = self._get_distractors(word_data["id"], limit=2)
            
            self.queue.append({
                "activity": "audio_mc_to_geo",
                "target": word_data,
                "distractors": [d[1] for d in distractors] # Georgian script strings
            })

        # Phase 3: Dialogue Context Reading
        for d in dialogues:
            dialogue_data = {"id": d[0], "code": d[1]}
            self.queue.append({
                "activity": "dialogue_passive",
                "target": dialogue_data
            })

        # Phase 4: Active Hard Production (The Recall Target)
        for m in monologues:
            word_data = {"id": m[0], "geo": m[1], "eng": m[2], "trans": m[3]}
            self.queue.append({
                "activity": "type_georgian",
                "target": word_data
            })
            
        self.total_exercises = len(self.queue)



    # ==========================================
    # 3. THE ADAPTIVE QUEUE LOGIC
    # ======================================
    def get_next_exercise(self):
        """Peeks at the top card in the queue."""
        if not self.queue:
            return None
        return self.queue[0]

    def submit_answer(self, is_correct):
        """
        Handles results. Pops the item. If incorrect, shoves an instructive
        intro card right in front and copies the failed card 3 slots deep.
        """
        current_exercise = self.queue.pop(0)

        if is_correct:
            # Only count items originally in the sequence towards true progress
            if current_exercise["activity"] != "card_intro":
                self.completed_count += 1
            
            progress = (self.completed_count / self.total_exercises) if self.total_exercises > 0 else 1.0
            return {"status": "correct", "progress": min(progress, 1.0)}
        else:
            # --- THE LOOP-UNTIL-CORRECT ADAPTIVE MECHANIC ---
            # 1. Force an instant educational look at the card if they failed it
            if current_exercise["activity"] != "card_intro":
                review_card = {
                    "activity": "card_intro",
                    "target": current_exercise["target"]
                }
                self.queue.insert(0, review_card)
                
                # 2. Push the actual quiz challenge 3 slots back into the active deck
                insert_index = min(3, len(self.queue))
                self.queue.insert(insert_index, current_exercise)
            
            progress = (self.completed_count / self.total_exercises) if self.total_exercises > 0 else 0.0
            return {"status": "failed", "progress": progress}



# ==========================================
# 4. TERMINAL PLAYBACK HARNESS (TEST RIG)
# ========================================
def run_terminal_lesson(session):
    """Accepts a fully initialized LessonSession object and runs it."""
    print("=" * 50)
    print(f"🌟 STARTING TERMINAL PLAYTEST FOR LESSON 🌟")
    print(f"📍 Coordinates: Phase {session.phase_num} | Unit {session.unit_num} | Lesson {session.lesson_num}")
    print(f"Total Master Exercises Generated: {session.total_exercises}")
    print("=" * 50)


    while True:
        card = session.get_next_exercise()
        if not card:
            print("\n🎉 VICTORY! Lesson Cleared Successfully with 100% Mastery!")
            break
            
        activity = card["activity"]
        target = card["target"]
        
        print("\n" + "-"*30)
        
        # --- SCREEN RENDERER SIMULATOR ---
        if activity == "mc_geo_to_eng":
            print(f"📝 MULTIPLE CHOICE (Geo -> Eng)")
            print(f"Georgian Word:  \033[1;36m{target['geo']}\033[0m")
            
            # Combine target and distractors, then shuffle options safely
            options = [target["eng"]] + card["distractors"]
            random.shuffle(options)
            
            for i, opt in enumerate(options, 1):
                print(f"  [{i}] {opt}")
                
            ans = input("Your Choice (1-3): ").strip()
            # Verify if their chosen string matches the target English translation
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["eng"])
            
        elif activity == "audio_mc_to_geo":
            print(f"🔊 LISTENING MC (Simulated Audio Trigger)")
            print(f"[AUDIO FILE PLAYING]: '{target['geo']}' Pronunciation Guide")
            print(f"Question: Match what you heard to the correct script:")
            
            options = [target["geo"]] + card["distractors"]
            random.shuffle(options)
            
            for i, opt in enumerate(options, 1):
                print(f"  [{i}] {opt}")
                
            ans = input("Your Choice (1-3): ").strip()
            idx = int(ans) - 1 if ans.isdigit() and 0 < int(ans) <= len(options) else -1
            is_correct = (idx != -1 and options[idx] == target["geo"])

        elif activity == "type_georgian":
            print(f"⌨️ PRODUCTION CRITICAL (Type in Georgian Script)")
            print(f"English Meaning: \033[1;33m{target['eng']}\033[0m")
            print(f"Hint Transliteration: {target['trans']}")
            
            ans = input("Type Georgian characters: ").strip()
            # Basic sanitization removing trailing spaces/punctuation comparisons
            is_correct = (ans.replace("!","").replace(".","") == target["geo"].replace("!","").replace(".",""))

        elif activity == "dialogue_passive":
            print(f"💬 DIALOGUE STUDY COMPONENT: [{target['code']}]")
            lines = session.get_dialogue_lines(target["id"])
            if not lines:
                print("  [Dialogue script content empty or dialogue_lines table unpopulated]")
                    
            for speaker, geo, trans, eng in lines:
                # Fallback filters to handle any minor punctuation mismatches gracefully
                display_trans = f" ({trans})" if trans else ""
                display_eng = f" -> {eng}" if eng else " -> [Translation Match Pending]"
                        
                print(f"  Speaker {speaker}: {geo}{display_trans}{display_eng}")
                        
            input("\nPress [ENTER] when you are finished reading the conversation to continue...")
            is_correct = True

        elif activity == "card_intro":
            print(f"⚠️ REVIEW BUFFER CARD (Study the details carefully!)")
            print(f"  🇬🇪 Georgian:       {target['geo']}")
            print(f"  🔤 Transliteration: {target['trans']}")
            print(f"  🇬🇧 English:        {target['eng']}")
            input("\nPress [ENTER] to acknowledge and re-queue the test module...")
            is_correct = True # Review acknowledgement steps always pass forward

        # --- EVALUATION LOGIC SUBMISSION ---
        res = session.submit_answer(is_correct)
        if activity not in ["card_intro", "dialogue_passive"]:
            if res["status"] == "correct":
                print("\033[1;32m✅ CORRECT!\033[0m")
            else:
                print("\033[1;31m❌ WRONG ANWER!\033[0m Re-shuffling card back into deck...")
                
        print(f"Current Lesson Queue Size: {len(session.queue)} Cards | Progress: {res['progress']*100:.1f}%")


if __name__ == "__main__":
    DATABASE_NAME = "database/content_poolbook.db"
        
    # Initialize the session object with curriculum coordinates
    active_session = LessonSession(
        db_path=DATABASE_NAME, 
        phase_num=1, 
        unit_num=1, 
        lesson_num=2
    )

    # Pass the entire active state machine directly to the player loop
    run_terminal_lesson(active_session)


