import sqlite3
import random
import os
import datetime
import time

class LessonSession:
    #  Default parameters to None to allow 100% automated lesson routing!
    def __init__(self, db_name="content_poolbook.db", phase_num=None, unit_num=None, lesson_num=None):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.project_root, "database", db_name)
        self.progress_db_path = os.path.join(self.project_root, "database", "user_progress.db")


        # If coordinates aren't provided, auto-discover where the user left off
        if phase_num is None or unit_num is None or lesson_num is None:
            resolved_id, p, u, l = self.get_next_automated_lesson()
            self.phase_num = p
            self.unit_num = u
            self.lesson_num = l
            self.lesson_id = resolved_id
        else:
            self.phase_num = phase_num
            self.unit_num = unit_num
            self.lesson_num = lesson_num
            self.lesson_id = None # Will resolve in _resolve_lesson_id() (# Resolved dynamically via helper)

        # Game State
        self.queue = []            
        self.total_exercises = 0   
        self.completed_count = 0
        
        # Initialize the deck
        self._build_session()

    # ==========================================
    # 1. DATABASE FETCHING & DISTRACTORS
    # ====================================



    def _resolve_lesson_id(self):
        """Resolves and caches the internal primary key lesson_id from curriculum sequence coordinates."""
        if getattr(self, 'lesson_id', None) is not None:
            return self.lesson_id
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.lesson_id 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            WHERE p.sequence_order = ? AND u.sequence_order = ? AND l.sequence_order = ?
        """, (self.phase_num, self.unit_num, self.lesson_num))
        res = cursor.fetchone()
        conn.close()
        
        if res:
            self.lesson_id = res[0]
        return self.lesson_id
    




    def _get_distractors(self, correct_content_id, limit=2):
        """
        Dynamically generates high-quality distractors.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        distractors = [] # Will store: (english, georgian)
        lesson_id = self._resolve_lesson_id()
        
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





    def _get_convo_distractors(self, correct_response_id, limit=2):
        """
        Pulls contextually safe conversational distractors by strictly filtering 
        for content tagged as 'response' in the tags table.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        distractors = []
        lesson_id = self._resolve_lesson_id()
        
        try:
            # TIER 1: Pull 'response' tags from the same Unit
            cursor.execute("""
                SELECT DISTINCT c.georgian, c.english 
                FROM content c
                JOIN content_tags ct ON c.content_id = ct.content_id
                JOIN tags t ON ct.tag_id = t.tag_id
                JOIN lesson_contents lc ON c.content_id = lc.associated_id
                JOIN lessons l ON lc.lesson_id = l.lesson_id
                WHERE t.name = 'response' 
                  AND l.unit_id = (SELECT unit_id FROM lessons WHERE lesson_id = ?)
                  AND c.content_id != ?
                ORDER BY RANDOM() LIMIT ?
            """, (lesson_id, correct_response_id, limit))
            
            distractors.extend(cursor.fetchall())
            
            # TIER 2: Global Fallback for 'response' tags
            if len(distractors) < limit:
                needed = limit - len(distractors)
                picked_geo = [row[0] for row in distractors]
                
                query = """
                    SELECT DISTINCT c.georgian, c.english 
                    FROM content c
                    JOIN content_tags ct ON c.content_id = ct.content_id
                    JOIN tags t ON ct.tag_id = t.tag_id
                    WHERE t.name = 'response' AND c.content_id != ?
                """
                params = [correct_response_id]
                
                if picked_geo:
                    placeholders = ','.join(['?'] * len(picked_geo))
                    query += f" AND c.georgian NOT IN ({placeholders})"
                    params.extend(picked_geo)
                    
                query += " ORDER BY RANDOM() LIMIT ?"
                params.append(needed)
                
                cursor.execute(query, params)
                distractors.extend(cursor.fetchall())
                
        except Exception as e:
            print(f"⚠️ Convo distractor parsing error: {e}")
        finally:
            conn.close()
            
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
    




    def _should_fade_transliteration(self, content_id, mastery_threshold=3):
        """
        Checks user_progress.db to see if the user has mastered a word enough
        times to hide its transliteration helper.
        """
        # Connect to your new user progress tracking database
        conn = sqlite3.connect(self.progress_db_path)
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




    def _get_urgent_review_items(self, limit=3):
        """Fetches top overdue review items from the registry."""
        conn = sqlite3.connect(self.progress_db_path)
        cursor = conn.cursor()
        today_str = datetime.date.today().isoformat()
        
        cursor.execute("""
            SELECT content_id FROM srs_registry 
            WHERE next_review_date <= ? 
            ORDER BY ease_factor ASC, mastery_level ASC 
            LIMIT ?
        """, (today_str, limit))
        
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]





    def get_progress_percentage(self):
            """
            Calculates exactly how much green to fill in Flet Progress Bar.
            """
            if self.total_exercises == 0:
                return 0.0
            
            # Calculate fraction for the UI wrapper
            return min(self.completed_count / self.total_exercises, 1.0)
    



    def _space_out_activities(self, activities):
        """
        Enforces absolute variance: guarantees consecutive exercises never 
        test the exact same vocabulary or phrase item ID.
        """
        if len(activities) <= 1:
            return activities

        random.shuffle(activities)
        spaced_list = []
        leftovers = []
        
        while activities:
            card = activities.pop(0)
            card_id = card.get("content_id")
            last_id = spaced_list[-1].get("content_id") if spaced_list else None
            
            if card_id != last_id:
                spaced_list.append(card)
            else:
                found_idx = -1
                for idx, next_card in enumerate(activities):
                    if next_card.get("content_id") != last_id:
                        found_idx = idx
                        break
                
                if found_idx != -1:
                    spaced_list.append(activities.pop(found_idx))
                    activities.insert(0, card)
                else:
                    leftovers.append(card)
        
        for card in leftovers:
            card_id = card.get("content_id")
            inserted = False
            for idx in range(len(spaced_list) + 1):
                prev_id = spaced_list[idx-1].get("content_id") if idx > 0 else None
                next_id = spaced_list[idx].get("content_id") if idx < len(spaced_list) else None
                if card_id != prev_id and card_id != next_id:
                    spaced_list.insert(idx, card)
                    inserted = True
                    break
            if not inserted:
                spaced_list.append(card)
                
        return spaced_list




    def _safe_stitch_waves(self, ordered_waves):
        """
        Stitches separate pedagogical waves together sequentially. If the last card 
        of Wave 1 matches the first card of Wave 2, it performs a surgical swap to prevent clumping.
        """
        stitched_stream = []
        for wave in ordered_waves:
            while wave:
                card = wave.pop(0)
                if stitched_stream and stitched_stream[-1].get("content_id") == card.get("content_id"):
                    # Boundary collision detected! Find an alternative item inside the incoming wave
                    found = False
                    for i, alternate in enumerate(wave):
                        if alternate.get("content_id") != stitched_stream[-1].get("content_id"):
                            stitched_stream.append(wave.pop(i))
                            wave.insert(0, card)  # Push colliding card back to step forward next
                            found = True
                            break
                    if not found:
                        stitched_stream.append(card)
                else:
                    stitched_stream.append(card)
        return stitched_stream
    



    def _get_last_production_style(self, content_id):
        """
        Queries log records to find out whether type_georgian or audio_dictation 
        was the most recent production format tested for this word.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT activity_type FROM activity_logs 
                WHERE content_id = ? AND activity_type IN ('type_georgian', 'audio_dictation')
                ORDER BY timestamp DESC LIMIT 1
            """, (content_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.OperationalError:
            # Fallback if logs table layout differs slightly
            return None
        finally:
            conn.close()






    # ==========================================
    # 2. THE PLAYLIST GENERATION TEMPLATE
    # ====================================
    def _build_session(self):
        """
        Translates database rows into an interactive queue of exercises. 
        Words are parsed chronologically, and their interactive testing 
        variants are shuffled/interleaved between dialogue milestones for optimal cognitive memory retention.
        """
        lesson_id = self._resolve_lesson_id()
        
        if not lesson_id:
            print(f"[!] Warning: Coordinate mapping failed for Phase {self.phase_num} Unit {self.unit_num}")            
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()


        # Extract chronological structural configuration directly from the curriculum table
        cursor.execute("""
            SELECT lc.step_order, lct.name, lc.associated_id
            FROM lesson_contents lc
            JOIN lesson_component_types lct ON lc.component_type_id = lct.component_type_id
            WHERE lc.lesson_id = ?
            ORDER BY lc.step_order ASC
        """, (lesson_id,))
        raw_steps = cursor.fetchall()


        # --- REFINED PEDAGOGICAL SUB-BUCKETS ---
        vocab_w1_recognition = []  # Phase 1: Multiple Choices
        vocab_w2_audio = []        # Phase 2: Audio Identification
        vocab_w3_production = []   # Phase 3: Dictation & Native Typing
        
        phrase_bucket = []
        matrix_bucket = []
        dialogue_bucket = []
        vocab_buffer = []  # For matrix grouping

        
        for step_num, comp_type, assoc_id in raw_steps:
            if comp_type == 'monologue':
                # Pull vocabulary item
                cursor.execute("SELECT content_id, georgian, english, transliteration FROM content WHERE content_id = ?", (assoc_id,))
                word_row = cursor.fetchone()
                if word_row:
                    c_id, geo, eng, trans = word_row

                    display_trans = trans if not self._should_fade_transliteration(c_id) else None
                    word_data = {"id": c_id, "geo": geo, "eng": eng, "trans": display_trans}                    
                    
                    distractors = self._get_distractors(word_data["id"], limit=2)
                    vocab_buffer.append(word_data) # Save for matrix
                    

                    # Phrase classification branch if length is long
                    if len(eng.split()) >= 3:
                        # For long phrase expressions, maintain simple progressive placement
                        phrase_bucket.append({
                            "content_id": c_id, 
                            "step_order": step_num,
                            "activity": "mc_geo_to_eng", 
                            "target": word_data, 
                            "distractors": [d[0] for d in distractors]
                        })
                        phrase_bucket.append({
                            "content_id": c_id, 
                            "step_order": step_num,
                            "activity": "type_georgian", 
                            "target": word_data
                        })
                        continue


                    # --- ADDING THE NEW BLUEPRINT ACTIVITIES ---
                
                    # --- WAVE DISTRIBUTION FOR CORE VOCABULARY ---
                    
                    # --- WAVE 1: ADAPTIVE RECOGNITION ---
                    # --- ADAPTIVE WAVE 1: RECOGNITION ---
                    # We inject a linked pairing tag so runtime can drop the sibling card if this one passes
                    vocab_w1_recognition.append({
                        "content_id": c_id, 
                        "step_order": step_num, 
                        "activity": "mc_geo_to_eng",
                        "target": word_data, 
                        "distractors": [d[0] for d in distractors],
                        "adaptive_pair_tag": f"recog_sibling_{c_id}" # Handshake link
                    })
                    vocab_w1_recognition.append({
                        "content_id": c_id, 
                        "step_order": step_num, 
                        "activity": "mc_eng_to_geo",
                        "target": word_data, 
                        "distractors": [d[1] for d in distractors],
                        "adaptive_pair_tag": f"recog_sibling_{c_id}",
                        "is_conditional_backup": True # Marked as secondary
                    })



                    # --- ADAPTIVE WAVE 2: AUDIO ---
                    # Only pick ONE style per lesson to immediately cut volume by 50%
                    chosen_audio_style = random.choice(["audio_mc_to_eng", "audio_mc_to_geo"])
                    chosen_distractors = [d[0] for d in distractors] if chosen_audio_style == "audio_mc_to_eng" else [d[1] for d in distractors]

                    # WAVE 2: AUDIO FAMILIARIZATION (Listening Skills)

                    vocab_w2_audio.append({
                        "content_id": c_id,
                        "step_order": step_num,
                        "activity": chosen_audio_style,
                        "target": word_data,
                        "distractors": chosen_distractors 
                    })


                    # --- ADAPTIVE WAVE 3: PRODUCTION ---
                    # Check historical logs to see which style hasn't been exposed yet
                    last_style_used = self._get_last_production_style(c_id)
                    
                    # Alternate types: if dictation was used last time during review, use typing now
                    next_production_style = "type_georgian" if last_style_used == "audio_dictation" else "audio_dictation"
                    
                    vocab_w3_production.append({
                        "content_id": c_id, 
                        "step_order": step_num, 
                        "activity": next_production_style, 
                        "target": word_data
                    })




            elif comp_type == 'convo_pair':
                # Fetch the Prompt and the Correct Response IDs from convo_pairs table
                # Here, assoc_id in lesson_contents represents the primary key of the convo_pair row
                cursor.execute("""
                    SELECT cp.prompt_id, cp.response_id, 
                            p.georgian, p.english, r.georgian, r.english
                    FROM convo_pairs cp
                    JOIN content p ON cp.prompt_id = p.content_id
                    JOIN content r ON cp.response_id = r.content_id
                    WHERE cp.pair_id = ? 
                """, (assoc_id,)) # Replace 'pair_id' with whatever your PK is named in convo_pairs
                    
                pair_row = cursor.fetchone()

                if pair_row:
                    p_id, r_id, p_geo, p_eng, r_geo, r_eng = pair_row
                    
                    # Fetch safe 'response' distractors using the new method
                    convo_distractors = self._get_convo_distractors(r_id, limit=2)
                        
                    phrase_bucket.append({
                        "content_id": f"pair_{assoc_id}",
                        "step_order": step_num,
                        "activity": "mc_geo_pair_geo",
                        "target": {
                            "prompt_geo": p_geo,
                            "prompt_eng": p_eng,
                            "correct_geo": r_geo,
                            "correct_eng": r_eng
                        },
                        # Distractors payload only needs the Georgian text
                        "distractors": [d[0] for d in convo_distractors] 
                    })



                    
            elif comp_type == 'dialogue':
                # --- GENERATE MATRIX BEFORE DIALOGUE ---
                # Group our buffered words into sets of 3 for the Match Matrix
                while len(vocab_buffer) >= 3:
                    matrix_targets = [vocab_buffer.pop(0) for _ in range(3)]
                    matrix_bucket.append({
                        "content_id": "matrix_block",
                        "step_order": step_num - 0.01,
                        "activity": "match_matrix_3x3",
                        "targets": matrix_targets # Contains 3 words!
                    })

                # Shuffle vocab before hitting a dialogue checkpoint
                #random.shuffle(activity_pool)
                #final_queue.extend(activity_pool)
                #activity_pool = [] # Clear the pool for words appearing after the dialogue

                # Insert the passive dialogue study frame at its exact chronological milestone position                
                cursor.execute("SELECT dialogue_id, internal_code FROM dialogues WHERE dialogue_id = ?", (assoc_id,))
                diag_row = cursor.fetchone()
                if diag_row:
                    dialogue_id = diag_row[0]
                    dialogue_data = {"id": dialogue_id, "code": diag_row[1]}

                    dialogue_bucket.append({
                        "content_id": f"diag_{dialogue_id}",
                        "step_order": step_num,
                        "activity": "dialogue_passive",
                        "target": dialogue_data
                    })
                
                    # Fetch all lines of this dialogue to generate dynamic questions
                    lines = self.get_dialogue_lines(dialogue_id)
                    
                    if len(lines) >= 2:
                        # 2. Dialogue Roleplay MC
                        # Hide the LAST line of the dialogue. Ask the user to complete it.
                        last_line = lines[-1] 
                        speaker, geo, trans, eng = last_line
                        
                        # We use convo distractors to get plausible sounding alternative responses
                        # We need the content_id of this line to get perfect distractors, 
                        # but for a dynamic generation fallback, we can pull random responses
                        roleplay_distractors = self._get_convo_distractors(correct_response_id=0, limit=2)

                        dialogue_bucket.append({
                            "content_id": f"diag_{dialogue_id}_rp",
                            "step_order": step_num + 0.1, # Just to keep it ordered right after passive
                            "activity": "dialogue_roleplay_mc",
                            "target": {
                                "speaker": speaker,
                                "correct_geo": geo,
                                "context_eng": eng
                            },
                            "distractors": [d[0] for d in roleplay_distractors]
                        })

                        # 3. Dialogue Context MC
                        # Pick a random line from the dialogue and test its meaning in context
                        random_line = random.choice(lines)
                        _, context_geo, _, context_eng = random_line
                        
                        # Grab some random English distractors globally
                        cursor.execute("SELECT english FROM content WHERE english != ? ORDER BY RANDOM() LIMIT 2", (context_eng,))
                        context_distractors = [row[0] for row in cursor.fetchall()]

                        dialogue_bucket.append({
                            "content_id": f"diag_{dialogue_id}_comp",
                            "step_order": step_num + 0.2,
                            "activity": "dialogue_context_mc",
                            "target": {
                                "quote_geo": context_geo,
                                "correct_eng": context_eng
                            },
                            "distractors": context_distractors
                        })

                
                    
        conn.close()

        # Flush remaining matrix variants at the end of the lesson
        while len(vocab_buffer) >= 3:
            matrix_targets = [vocab_buffer.pop(0) for _ in range(3)]
            matrix_bucket.append({
                "content_id": "matrix_block",
                "step_order": 999,
                "activity": "match_matrix_3x3",
                "targets": matrix_targets 
            })

        # --- PROCESS WAVES INDIVIDUALLY TO PREVENT CLUMPING ---
        cleaned_w1 = self._space_out_activities(vocab_w1_recognition)
        cleaned_w2 = self._space_out_activities(vocab_w2_audio)
        cleaned_w3 = self._space_out_activities(vocab_w3_production)
        cleaned_phrases = self._space_out_activities(phrase_bucket)

        # Stitch vocabulary waves securely using the boundary checker
        ordered_vocab_stream = self._safe_stitch_waves([cleaned_w1, cleaned_w2, cleaned_w3])

        # Combine Vocabs and Phrases into our core learning timeline
        core_learning_stream = ordered_vocab_stream + cleaned_phrases
        final_learning_stream = []


        # --- SMART REVIEW INTERLEAVING SYSTEM ---
        urgent_ids = self._get_urgent_review_items(limit=3)
        
        if urgent_ids:
            # Open content database to quickly load the text for the review words
            print(f"🧠 SRS Intercept: Interleaving {len(urgent_ids)} active review challenges...")
            content_conn = sqlite3.connect(self.db_path)
            content_cursor = content_conn.cursor()
            
            new_card_counter = 0
            for card in core_learning_stream:
                final_learning_stream.append(card)
                if card.get("activity") not in ["card_intro", "dialogue_passive"]:
                    new_card_counter += 1
                
                # Every 3 learning steps, seamlessly insert an overdue review card
                if new_card_counter >= 3 and urgent_ids:
                    rev_id = urgent_ids.pop(0)
                    content_cursor.execute("SELECT english, georgian, transliteration FROM content WHERE content_id = ?", (rev_id,))
                    word_row = content_cursor.fetchone()
                    
                    if word_row:
                        eng, geo, trans = word_row
                        final_learning_stream.append({
                            "content_id": rev_id,
                            "step_order": card.get("step_order", 0) + 0.05,
                            "activity": "type_georgian",
                            "is_review_item": True,
                            "target": {"id": rev_id, "eng": eng, "geo": geo, "trans": trans}
                        })
                    new_card_counter = 0


            # Catch any leftover review cards if the lesson was very short
            while urgent_ids:
                rev_id = urgent_ids.pop(0)
                content_cursor.execute("SELECT english, georgian, translit FROM content WHERE id = ?", (rev_id,))
                word_row = content_cursor.fetchone()
                if word_row:
                    eng, geo, trans = word_row
                    final_learning_stream.append({
                        "content_id": rev_id,
                        "step_order": 999, 
                        "activity": "type_georgian", 
                        "is_review_item": True,
                        "target": {"id": rev_id, "eng": eng, "geo": geo, "trans": trans}
                    })
                    
            content_conn.close()
        else:
            final_learning_stream = core_learning_stream
            
        # --- RIGID SEQUENTIAL CONCATENATION ---
        # 1. Vocabs & Phrases (with interspersed SRS) -> 2. All Matrix Grids -> 3. Story Dialogues
        self.queue = final_learning_stream + matrix_bucket + dialogue_bucket
        self.total_exercises = len(self.queue)




    def get_next_automated_lesson(self):
        """
        Scans the progress database to find the first incomplete lesson.
        If no progress exists, defaults to Phase 1, Unit 1, Lesson 1.
        """

        # 1. Connect to the progress tracker to see what is completed
        conn_prog = sqlite3.connect(self.progress_db_path)
        cursor_prog = conn_prog.cursor()
        try:
            # Ensure table exists so it doesn't crash on first run
            cursor_prog.execute("""
                CREATE TABLE IF NOT EXISTS lesson_progress (
                    lesson_id INTEGER PRIMARY KEY,
                    is_completed INTEGER DEFAULT 0
                )
            """)
            cursor_prog.execute("SELECT lesson_id FROM lesson_progress WHERE is_completed = 1")
            completed_lessons = [row[0] for row in cursor_prog.fetchall()]
        except Exception as e:
            print(f"⚠️ AUTOMATED ROUTING ERROR: {e}") # Expose the real error!
            completed_lessons = []
        finally:
            conn_prog.close()
                
        # 2. Connect to your content poolbook to find the next chronological lesson
        conn_content = sqlite3.connect(self.db_path)
        cursor_content = conn_content.cursor()

        cursor_content.execute("""
            SELECT l.lesson_id, p.sequence_order, u.sequence_order, l.sequence_order 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            ORDER BY p.sequence_order ASC, u.sequence_order ASC, l.sequence_order ASC
        """)
        all_lessons = cursor_content.fetchall()
            
        # Find the very first lesson ID that doesn't exist in the 'completed' list
        for lesson_id, p_num, u_num, l_num in all_lessons:
            if lesson_id not in completed_lessons:
                cursor_content.execute("SELECT COUNT(*) FROM lesson_contents WHERE lesson_id = ?", (lesson_id,))
                if cursor_content.fetchone()[0] > 0:
                    conn_content.close()
                    return lesson_id, p_num, u_num, l_num

        conn_content.close()

        # Fallback: If everything is completed, default back to the first lesson
        if all_lessons:
            return all_lessons[0][0], all_lessons[0][1], all_lessons[0][2], all_lessons[0][3]
        return 1, 1, 1, 1




    # ==========================================
    # 3. QUEUE LOGIC & PROGRESS LOGGING
    # ======================================
    def get_next_exercise(self):
        """Peeks at the top card in the queue."""
        if not self.queue:
            return None
        # Start the high-precision stopwatch right before returning the active card
        self.card_start_time = time.perf_counter()
        return self.queue[0]




    def submit_answer(self, is_correct):
        """
        Processes an answer submission, updates the queue, and automatically logs 
        telemetry and SRS updates directly into user_progress.db.
        """
        # Stop the clock instantly
        elapsed_time = time.perf_counter() - getattr(self, "card_start_time", time.perf_counter())
        latency_ms = int(elapsed_time * 1000)

        # Grab the active card before mutating the queue or state
        # (Adapting to how your engine tracks the current active card index/object)
        current_card = self.get_next_exercise()
        
        if current_card and "target" in current_card:
            content_id = current_card["target"].get("id", 0)
            activity_type = current_card.get("activity", "unknown")
            is_review = current_card.get("is_review_item", False)

            # Skip passive study states or setup frames so logs contain pure metrics
            if activity_type not in ["card_intro", "dialogue_passive"] and content_id is not None:
                # 🌟 CALL THE LOGGER ROUTINE HERE AUTOMATICALLY!
                self.log_user_response(content_id, is_correct, activity_type, is_review=is_review, latency_ms=latency_ms)

        if is_correct:
            # Answered perfectly! Permanently cycle it off the active stack
            if self.queue:
                self.queue.pop(0) # Remove successful card
            self.completed_count += 1
            status = "correct"

            # Trigger full lesson completion logging when the deck size clears
            if not self.queue:
                self._mark_lesson_completed()

        else:
            status = "incorrect"
            if self.queue:
                failed_card = self.queue.pop(0)
                
                # --- ADAPTIVE CORRECTION MUTATION ENGINE ---
                old_activity = failed_card.get("activity")
                mutated = False
                
                # Swap recognition directions on failure and recalculate distractor targets!
                if old_activity == "mc_geo_to_eng":
                    failed_card["activity"] = "mc_eng_to_geo"
                    distractors = self._get_distractors(content_id, limit=2)
                    failed_card["distractors"] = [d[1] for d in distractors]
                    mutated = True
                elif old_activity == "mc_eng_to_geo":
                    failed_card["activity"] = "mc_geo_to_eng"
                    distractors = self._get_distractors(content_id, limit=2)
                    failed_card["distractors"] = [d[0] for d in distractors]
                    mutated = True
                # Swap listening MC styles
                elif old_activity == "audio_mc_to_eng":
                    failed_card["activity"] = "audio_mc_to_geo"
                    distractors = self._get_distractors(content_id, limit=2)
                    failed_card["distractors"] = [d[1] for d in distractors]
                    mutated = True
                elif old_activity == "audio_mc_to_geo":
                    failed_card["activity"] = "audio_mc_to_eng"
                    distractors = self._get_distractors(content_id, limit=2)
                    failed_card["distractors"] = [d[0] for d in distractors]
                    mutated = True
                # Swap production typing / dictation
                elif old_activity == "type_georgian":
                    failed_card["activity"] = "audio_dictation"
                    mutated = True
                elif old_activity == "audio_dictation":
                    failed_card["activity"] = "type_georgian"
                    mutated = True

                if mutated:
                    print(f"🔄 Adaptive Correction: Swapping failed card '{old_activity}' to equivalent '{failed_card['activity']}'")

                self.queue.insert(min(3, len(self.queue)), failed_card)      
        
        # Calculate matching fraction metrics for your test rig's `res['progress']` key
        total = max(self.total_exercises, 1)
        return {"status": status, "progress": max(0.0, min(self.completed_count / total, 1.0))}





    def handle_correct_answer(self, completed_card):
        """
        Executes when an active card passes validation. 
        Surgically prunes the alternative direction sibling card from the queue,
        regardless of which card was shuffled first.
        """
        pair_tag = completed_card.get("adaptive_pair_tag")
        
        if pair_tag:
            # Search the upcoming queue (starting at index 1 to ignore the active card)
            for idx in range(1, len(self.queue)):
                upcoming_card = self.queue[idx]
                
                # If we find the sibling card sharing the same pair tag, prune it!
                if upcoming_card.get("adaptive_pair_tag") == pair_tag:
                    print(f"⚡ Adaptive Engine: Sibling card mastery confirmed! Pruning redundant card position {idx} from active layout.")
                    
                    pruned_card = self.queue.pop(idx)
                    pruned_id = pruned_card.get("target", {}).get("id")
                    
                    # Log it as an SRS review item so it's tested in future sessions
                    if pruned_id:
                        self.register_pruned_card_to_srs(pruned_id)

                    self.total_exercises -= 1
                    break

                    


    def register_pruned_card_to_srs(self, content_id):
        """Forces any bypassed/pruned cards into the SRS review registry."""
        conn = sqlite3.connect(self.progress_db_path)
        cursor = conn.cursor()
        try:
            today_str = datetime.date.today().isoformat()
            cursor.execute("""
                INSERT OR IGNORE INTO srs_registry (content_id, mastery_level, ease_factor, repetitions, interval_days, next_review_date)
                VALUES (?, 0, 2.5, 0, 0, ?)
            """, (content_id, today_str))
            conn.commit()
        except Exception as e:
            print(f"⚠️ SRS registration on pruned card failed: {e}")
        finally:
            conn.close()




    def log_user_response(self, content_id, is_correct, activity_type="mc_geo_to_eng", is_review=False, latency_ms=0):
        conn = sqlite3.connect(self.progress_db_path)        
        cursor = conn.cursor()
            
        try:
            # Added response_latency_ms field to schema automatically
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_activity_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT, phase_num INTEGER, unit_num INTEGER, 
                    lesson_num INTEGER, activity_type TEXT, content_id INTEGER, is_correct INTEGER,
                    is_review_item INTEGER, response_latency_ms INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS srs_registry (
                    content_id INTEGER PRIMARY KEY, mastery_level INTEGER, ease_factor REAL, 
                    repetitions INTEGER, interval_days INTEGER, next_review_date TEXT
                )
            """)

            # Insert the latency record directly
            cursor.execute("""
                INSERT INTO research_activity_log (phase_num, unit_num, lesson_num, activity_type, content_id, is_correct, is_review_item, response_latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.phase_num, self.unit_num, self.lesson_num, activity_type, content_id, 1 if is_correct else 0, 1 if is_review else 0, latency_ms))

            if content_id and content_id > 0:
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
                        ease_factor = min(3.0, max(1.3, old_ef + 0.1))
                        if is_review:
                            interval_days = 1 if repetitions == 1 else (6 if repetitions == 2 else int(old_interval * ease_factor))
                        else:
                            interval_days = max(1, old_interval)
                    else:
                        repetitions = 0
                        interval_days = 0
                        ease_factor = max(1.3, old_ef - 0.2)
                    
                interval_days = min(120, interval_days)
                next_date = (datetime.date.today() + datetime.timedelta(days=interval_days)).isoformat()
                    
                cursor.execute("""
                    INSERT OR REPLACE INTO srs_registry (content_id, mastery_level, ease_factor, repetitions, interval_days, next_review_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (content_id, repetitions, ease_factor, repetitions, interval_days, next_date))
                
            conn.commit()
        except Exception as e:
            print(f"❌ Tracking Engine Error: {e}")
        finally:
            conn.close()
    

    def _mark_lesson_completed(self):
        """Commits full lesson milestone clearance items into user_progress.db tracking tables."""
        
        conn = sqlite3.connect(self.progress_db_path)
        cursor = conn.cursor()
        try:
            lesson_id = self._resolve_lesson_id()
            if lesson_id:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS lesson_progress (
                        lesson_id INTEGER PRIMARY KEY,
                        is_completed INTEGER DEFAULT 0
                    )
                """)
                cursor.execute("""
                    INSERT OR REPLACE INTO lesson_progress (lesson_id, is_completed)
                    VALUES (?, 1)
                """, (lesson_id,))
                conn.commit()
        except Exception as e:
            print(f"❌ PROGRESS LOG ERROR: {e}")
        finally:
            conn.close()
        
