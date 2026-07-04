import sqlite3
import random
import os

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

        # Track the internal lesson ID after resolving coordinates
        self.lesson_id = None
        
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
            
        self.lesson_id = res[0]

        # 2. Step 2: Fetch Monologues using the resolved internal ID
        cursor.execute("""
            SELECT c.content_id, c.georgian, c.english, c.transliteration 
            FROM lesson_contents lc
            JOIN lesson_component_types lct ON lc.component_type_id = lct.component_type_id
            JOIN content c ON lc.associated_id = c.content_id
            WHERE lc.lesson_id = ? AND lct.name = 'monologue'
        """, (self.lesson_id,))
        monologues = cursor.fetchall()

        # 3. Step 3: Fetch Dialogues
        cursor.execute("""
            SELECT d.dialogue_id, d.internal_code 
            FROM lesson_contents lc
            JOIN lesson_component_types lct ON lc.component_type_id = lct.component_type_id
            JOIN dialogues d ON lc.associated_id = d.dialogue_id
            WHERE lc.lesson_id = ? AND lct.name = 'dialogue'
        """, (self.lesson_id,))
        dialogues = cursor.fetchall()
        
        conn.close()
        return monologues, dialogues
    

    def _get_distractors(self, correct_content_id, limit=2):
        """
        Dynamically generates high-quality distractors.
        Returns tuples mapped as (english, georgian) so d[0] displays full English words
        and d[1] satisfies your Georgian script checks on line 241.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        distractors = [] # Will store: (english, georgian)
        lesson_id = self.lesson_id
        
        if lesson_id:
            try:
                # TIER 1: Pull from other vocabulary items in this EXACT same lesson
                cursor.execute("""
                    SELECT DISTINCT c.english, c.georgian
                    FROM content c
                    JOIN lesson_contents lc ON c.content_id = lc.associated_id
                    WHERE lc.lesson_id = ? 
                      AND c.content_id != ? 
                      AND LENGTH(c.english) >= 2
                    ORDER BY RANDOM() LIMIT ?
                """, (lesson_id, correct_content_id, limit))
                distractors.extend(cursor.fetchall())
                
                # TIER 2: If we need more options, expand to the wider Unit
                if len(distractors) < limit:
                    needed = limit - len(distractors)
                    picked_english = [row[0] for row in distractors] # English is at index 0
                    
                    query = """
                        SELECT DISTINCT c.english, c.georgian
                        FROM content c
                        JOIN lesson_contents lc ON c.content_id = lc.associated_id
                        JOIN lessons l ON lc.lesson_id = l.lesson_id
                        WHERE l.unit_id = (SELECT unit_id FROM lessons WHERE lesson_id = ?)
                          AND c.content_id != ?
                          AND LENGTH(c.english) >= 2
                    """
                    params = [lesson_id, correct_content_id]
                    
                    if picked_english:
                        placeholders = ','.join(['?'] * len(picked_english))
                        query += f" AND c.english NOT IN ({placeholders})"
                        params.extend(picked_english)
                        
                    query += " ORDER BY RANDOM() LIMIT ?"
                    params.append(needed)
                    
                    cursor.execute(query, params)
                    distractors.extend(cursor.fetchall())
                    
            except Exception as e:
                print(f"⚠️ Tiered distractor parsing bypass: {e}")

        # TIER 3: Global Fallback with strict length guardrails
        if len(distractors) < limit:
            needed = limit - len(distractors)
            picked_english = [row[0] for row in distractors]
            
            query = """
                SELECT DISTINCT english, georgian FROM content 
                WHERE content_id != ? 
                  AND LENGTH(english) >= 2
            """
            params = [correct_content_id]
            
            if picked_english:
                placeholders = ','.join(['?'] * len(picked_english))
                query += f" AND english NOT IN ({placeholders})"
                params.extend(picked_english)
                
            query += " ORDER BY RANDOM() LIMIT ?"
            params.append(needed)
            
            cursor.execute(query, params)
            distractors.extend(cursor.fetchall())
            
        conn.close()
        
        # Return the exact limit requested, perfectly balanced as (english, georgian)
        return distractors[:limit]


    def get_dialogue_lines(self, dialogue_id):
        """Fetches the full script lines using your clean relational IDs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        #  Cleaned up to map dl.content_id directly to c.content_id ordered by line_order
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
    
    def build_chronological_playlist(self, lesson_id, unit_id):
        """
        Compiles the active lesson steps based on your strict Step_Order timeline.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pull steps matching your updated lesson_contents primary key structure
        cursor.execute("""
            SELECT lc.step_order, lct.name, lc.associated_id
            FROM lesson_contents lc
            JOIN lesson_component_types lct ON lc.component_type_id = lct.component_type_id
            WHERE lc.lesson_id = ?
            ORDER BY lc.step_order ASC
        """, (lesson_id,))
        
        raw_steps = cursor.fetchall()
        playlist = []
        
        for step_num, comp_type, assoc_id in raw_steps:
            if comp_type == 'monologue':
                # Fetch word data
                cursor.execute("SELECT content_id, georgian, transliteration, english FROM content WHERE content_id = ?", (assoc_id,))
                c_id, geo, trans, eng = cursor.fetchone()
                
                # Generate dynamic multiple choice options
                distractors = self.get_smart_distractors(c_id, unit_id, limit=3)
                choices = distractors + [eng]
                import random
                random.shuffle(choices) # Shuffle so correct answer isn't always last
                
                playlist.append({
                    "step_order": step_num,
                    "type": "vocabulary_challenge",
                    "content_id": c_id,
                    "georgian": geo,
                    "transliteration": trans,
                    "correct_answer": eng,
                    "choices": choices
                })
                
            elif comp_type == 'dialogue':
                playlist.append({
                    "step_order": step_num,
                    "type": "dialogue_passive",
                    "dialogue_id": assoc_id
                })
                
        conn.close()
        return playlist


    def _should_fade_transliteration(self, content_id, mastery_threshold=3):
        """
        Checks user_progress.db to see if the user has mastered a word enough
        times to hide its transliteration helper.
        """
        # Connect to your new user progress tracking database
        conn = sqlite3.connect("database/user_progress.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT repetitions FROM srs_registry WHERE content_id = ?
            """, (content_id,))
            res = cursor.fetchone()
            
            # If they have answered it correctly >= threshold times, hide it!
            if res and res[0] >= mastery_threshold:
                return True
        except Exception as e:
            print(f"⚠️ Progress database read bypass: {e}")
        finally:
            conn.close()
            
        return False


    def _inject_srs_reviews(self, base_playlist):
        """
        Scans for overdue flashcards and weaves them into the front of the active lesson.
        """
        import datetime
        
        progress_conn = sqlite3.connect("database/user_progress.db")
        progress_cursor = progress_conn.cursor()
        
        content_conn = sqlite3.connect(self.db_path)
        content_cursor = content_conn.cursor()
        
        today = datetime.date.today().isoformat()
        injected_steps = []
        
        try:
            # 1. Find overdue word content IDs
            progress_cursor.execute("""
                SELECT content_id FROM srs_registry 
                WHERE next_review_date <= ?
                ORDER BY mastery_level ASC, next_review_date ASC
                LIMIT 3
            """, (today,))
            
            overdue_items = progress_cursor.fetchall()
            
            # 2. Fetch the text assets for these words and build review steps
            for index, (c_id,) in enumerate(overdue_items):
                content_cursor.execute("""
                    SELECT georgian, transliteration, english FROM content WHERE content_id = ?
                """, (c_id,))
                word_res = content_cursor.fetchone()
                
                if word_res:
                    geo, trans, eng = word_res
                    
                    # Grab smart distractors for the review question
                    raw_distractors = self._get_distractors(c_id, limit=2)
                    
                    # Formulate an injection activity step object
                    review_step = {
                        "step_order": 0, # Denotes system injected review
                        "activity": "mc_geo_to_eng",
                        "target": {
                            "id": c_id,
                            "geo": geo,
                            "trans": trans,
                            "eng": eng,
                        },
                        "distractors": [d[0] for d in raw_distractors],
                        "is_review_item": True # Flagged for your logging telemetry
                    }
                    injected_steps.append(review_step)
                    
            if injected_steps:
                print(f"🧠 SRS Intercept: Injected {len(injected_steps)} overdue review cards into session.")
                
        except Exception as e:
            print(f"⚠️ SRS Injection failure: {e}")
        finally:
            progress_conn.close()
            content_conn.close()
            
        # Return the review items mixed cleanly at the top of your actual lesson items
        return injected_steps + base_playlist
    



    def get_progress_percentage(self, current_step_index):
            """
            Calculates exactly how much green to fill in Flet Progress Bar.
            """
            total_steps = self.total_excersises
            if total_steps == 0:
                return 0.0
            
            # Calculate fraction for the UI wrapper
            return min(current_step_index / total_steps, 1.0)
    


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

        # This weaves the smart review items seamlessly right at the start of the user's session.
        self.queue = self._inject_srs_reviews(self.queue)   
        
        # Recalculate total exercises AFTER injection so progress math stays accurate 
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
        Processes an answer submission, updates the queue, and automatically logs 
        telemetry and SRS updates directly into user_progress.db.
        """
        # 1. Grab the active card before mutating the queue or state
        # (Adapting to how your engine tracks the current active card index/object)
        current_card = self.get_next_exercise()
        
        if current_card and "target" in current_card:
            content_id = current_card["target"].get("id")
            activity_type = current_card.get("activity", "unknown")
            
            # Skip passive study states or setup frames so logs contain pure metrics
            if activity_type not in ["card_intro", "dialogue_passive"] and content_id is not None:
                # 🌟 CALL THE LOGGER ROUTINE HERE AUTOMATICALLY!
                self.log_user_response(content_id, is_correct, activity_type)

        if is_correct:
            # Answered perfectly! Permanently cycle it off the active stack
            if self.queue:
                self.queue.pop(0)
            self.completed_count += 1
            status = "correct"
        else:
            # Mistake made. Penalty: Pop off top and insert it 3 items down to ensure repetition
            status = "incorrect"
            if self.queue:
                failed_card = self.queue.pop(0)
                # Re-queue penalty distance buffer
                self.queue.insert(min(3, len(self.queue)), failed_card)        
        
        # Calculate matching fraction metrics for your test rig's `res['progress']` key
        total = max(self.total_exercises, 1)
        current_progress = self.completed_count / total
        
        return {
            "status": status,
            "progress": max(0.0, min(current_progress, 1.0))
        }
        

    def log_user_response(self, content_id, is_correct, activity_type="mc_geo_to_eng"):
        """
        Saves user results using absolute directory paths to prevent ghost DB files.
        """
        import datetime
            
        # Force the absolute path to your engine folder's project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_db_path = os.path.join(base_dir, "database/user_progress.db")
            
        print(f"\n🔍 DB Write Attempt: Target file path is: {target_db_path}")
            
        conn = sqlite3.connect(target_db_path)
        cursor = conn.cursor()
            
        try:
            p_num = self.phase_num
            u_num = self.unit_num
            l_num = self.lesson_id if self.lesson_id else 1
                
            # 1. WRITE ACTIVITY LOG
            cursor.execute("""
                INSERT INTO research_activity_log 
                (phase_num, unit_num, lesson_num, activity_type, content_id, is_correct)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p_num, u_num, l_num, activity_type, content_id, 1 if is_correct else 0))

            # 2. CALCULATE SRS INTERVALS
            cursor.execute("SELECT repetitions, ease_factor, interval_days FROM srs_registry WHERE content_id = ?", (content_id,))
            srs_row = cursor.fetchone()
                
            if not srs_row:
                repetitions = 1 if is_correct else 0
                ease_factor = 2.5
                interval_days = 1 if is_correct else 0
            else:
                old_reps, old_ef, old_interval = srs_row
                if is_correct:
                    repetitions = old_reps + 1
                    ease_factor = max(1.3, old_ef + 0.1)
                    interval_days = 1 if repetitions == 1 else (4 if repetitions == 2 else int(old_interval * ease_factor))
                else:
                    repetitions = 0
                    interval_days = 0
                    ease_factor = max(1.3, old_ef - 0.2)
                
            next_date = (datetime.date.today() + datetime.timedelta(days=interval_days)).isoformat()
                
            # 3. UPSERT INTO REGISTRY
            cursor.execute("""
                INSERT OR REPLACE INTO srs_registry 
                (content_id, mastery_level, ease_factor, repetitions, interval_days, next_review_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (content_id, repetitions, ease_factor, repetitions, interval_days, next_date))
                
            conn.commit()
            print(f"💾 DATABASE SUCCESS: Logged entry for content_id {content_id}! (Correct: {is_correct})")
                
        except Exception as e:
            print(f"❌ DATABASE CRITICAL ERROR: {e}")
        finally:
            conn.close()



    def get_next_automated_lesson():
        """Scans the progress database to find the first incomplete lesson."""
        
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. Connect to the progress tracker to see what is completed
        conn_prog = sqlite3.connect("database/user_progress.db")
        cursor_prog = conn_prog.cursor()
        
        cursor_prog.execute("SELECT lesson_id FROM lesson_progress WHERE is_completed = 1")
        completed_lessons = [row[0] for row in cursor_prog.fetchall()]
        conn_prog.close()
        
        # 2. Connect to your content book to find the next logical lesson matching your chronology
        conn_content = sqlite3.connect("database/content_poolbook.db")
        cursor_content = conn_content.cursor()
        
        # Grab all valid lessons in structural hierarchy order
        cursor_content.execute("""
            SELECT l.lesson_id, p.sequence_order, u.sequence_order, l.sequence_order 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            ORDER BY p.sequence_order ASC, u.sequence_order ASC, l.sequence_order ASC
        """)
        all_lessons = cursor_content.fetchall()
        conn_content.close()
        
        # Find the very first lesson ID that doesn't exist in the 'completed' list
        for lesson_id, p_num, u_num, l_num in all_lessons:
            if lesson_id not in completed_lessons:
                print(f"🎯 Automated Routing: Resuming at Phase {p_num}, Unit {u_num}, Lesson {l_num}")
                return lesson_id, p_num, u_num, l_num
                
        # Fallback: If everything is completed, return the last lesson or loop back
        return all_lessons[0][0], all_lessons[0][1], all_lessons[0][2], all_lessons[0][3]



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
                print("\033[1;31m❌ WRONG ANSWER!\033[0m Re-shuffling card back into deck...")
                
        print(f"Current Lesson Queue Size: {len(session.queue)} Cards | Progress: {res['progress']*100:.1f}%")


if __name__ == "__main__":
    DATABASE_NAME = "database/content_poolbook.db"
        
    # Initialize the session object with curriculum coordinates
    active_session = LessonSession(
        db_path=DATABASE_NAME, 
        phase_num=1, 
        unit_num=1, 
        lesson_num=1
    )

    # Pass the entire active state machine directly to the player loop
    run_terminal_lesson(active_session)
    


