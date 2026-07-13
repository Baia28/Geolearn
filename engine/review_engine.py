import sqlite3
import random
import os
import datetime
import time

class ReviewSession:
    def __init__(self, db_name="content_poolbook.db", max_items=12):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.project_root, "database", db_name)
        self.progress_db_path = os.path.join(self.project_root, "database", "user_progress.db")
        
        self.max_items = max_items
        self.queue = []
        self.total_exercises = 0
        self.completed_count = 0
        
        # Build the session immediately upon instantiation
        self._build_review_session()

    def _should_fade_transliteration(self, content_id, mastery_threshold=3):
        """Checks user_progress.db to see if the user has mastered a word enough to hide helpers."""
        conn = sqlite3.connect(self.progress_db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT repetitions FROM srs_registry WHERE content_id = ?", (content_id,))
            res = cursor.fetchone()
            if res and res[0] >= mastery_threshold:
                return True
        except Exception as e:
            print(f"⚠️ Progress database read bypass: {e}")
        finally:
            conn.close()
        return False

    def get_progress_percentage(self):
        """Calculates exact progress mapping for UI element tracking consistency."""
        if self.total_exercises == 0:
            return 0.0
        return min(self.completed_count / self.total_exercises, 1.0)

    def _get_review_content_ids(self, limit):
        """Fetches overdue items, or backfills with lowest mastery items if review queue is dry."""
        conn = sqlite3.connect(self.progress_db_path)
        cursor = conn.cursor()
        today_str = datetime.date.today().isoformat()
        
        # Priority 1: Get items actually due for review
        cursor.execute("""
            SELECT content_id FROM srs_registry 
            WHERE next_review_date <= ? 
            ORDER BY ease_factor ASC, mastery_level ASC 
            LIMIT ?
        """, (today_str, limit))
        review_ids = [row[0] for row in cursor.fetchall()]
        
        # Priority 2: Backfill with weakest items if user just wants extra optional practice
        if len(review_ids) < limit:
            needed = limit - len(review_ids)
            placeholders = ",".join(["?"] * len(review_ids)) if review_ids else "0"
            query = f"""
                SELECT content_id FROM srs_registry
                WHERE content_id NOT IN ({placeholders})
                ORDER BY mastery_level ASC, repetitions ASC
                LIMIT ?
            """
            params = review_ids + [needed] if review_ids else [needed]
            cursor.execute(query, params)
            backfill_ids = [row[0] for row in cursor.fetchall()]
            review_ids.extend(backfill_ids)
            
        conn.close()
        return review_ids

    def _get_distractors(self, correct_content_id, limit=2):
        """Generates global distractors out of the main dictionary pool."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT english, georgian FROM content 
            WHERE content_id != ? AND LENGTH(english) >= 2
            ORDER BY RANDOM() LIMIT ?
        """, (correct_content_id, limit))
        distractors = cursor.fetchall()
        conn.close()
        return distractors

    def _build_review_session(self):
        """Assembles a mixed, balanced deck entirely consisting of review elements."""
        target_ids = self._get_review_content_ids(self.max_items)
        if not target_ids:
            self.queue = []
            self.total_exercises = 0
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ",".join(["?"] * len(target_ids))
        cursor.execute(f"""
            SELECT content_id, english, georgian, transliteration 
            FROM content 
            WHERE content_id IN ({placeholders})
        """, target_ids)
        vocab_rows = cursor.fetchall()
        conn.close()

        activity_pool = []
        
        for c_id, eng, geo, trans in vocab_rows:
            # Apply the fading filter logic directly here
            display_trans = trans if not self._should_fade_transliteration(c_id) else None
            
            word_data = {"id": c_id, "eng": eng, "geo": geo, "trans": display_trans}
            distractors = self._get_distractors(c_id, limit=2)
            
            # Tier 1 Card: Receptive Multiple Choice (Shuffled types)
            if random.choice([True, False]):
                activity_pool.append({
                    "activity": "mc_geo_to_eng", "is_review_item": True,
                    "target": word_data, "distractors": [d[0] for d in distractors]
                })
            else:
                activity_pool.append({
                    "activity": "audio_mc_to_geo", "is_review_item": True,
                    "target": word_data, "distractors": [d[1] for d in distractors]
                })

            # Tier 2 Card: Active Production (Typing / Dictation recall)
            if random.choice([True, False]):
                activity_pool.append({
                    "activity": "type_georgian", "is_review_item": True, "target": word_data
                })
            else:
                activity_pool.append({
                    "activity": "audio_dictation", "is_review_item": True, "target": word_data
                })

        # Shuffle everything so words are perfectly interleaved
        random.shuffle(activity_pool)
        self.queue = activity_pool
        self.total_exercises = len(self.queue)

    def get_next_exercise(self):
        """Fetches the active prompt and initiates the response timer."""
        if not self.queue:
            return None
        self.card_start_time = time.perf_counter()
        return self.queue[0]

    def submit_answer(self, is_correct):
        """Updates internal scoring matrix counters and re-queues failed elements 3 slots down."""
        elapsed_time = time.perf_counter() - getattr(self, "card_start_time", time.perf_counter())
        latency_ms = int(elapsed_time * 1000)
        
        current_card = self.get_next_exercise()
        if current_card and "target" in current_card:
            content_id = current_card["target"].get("id", 0)
            activity_type = current_card.get("activity", "unknown")
            
            self.log_user_response(content_id, is_correct, activity_type, latency_ms)

        if is_correct:
            if self.queue:
                self.queue.pop(0)
            self.completed_count += 1
            status = "correct"
        else:
            status = "incorrect"
            if self.queue:
                failed_card = self.queue.pop(0)
                # Loop-until-mastered mechanic: slip it back in 3 slots down
                self.queue.insert(min(3, len(self.queue)), failed_card)

        return {"status": status, "progress": self.get_progress_percentage()}

    def log_user_response(self, content_id, is_correct, activity_type, latency_ms):
        """Adjusts calendar timestamps inside srs_registry based on performance metrics."""
        conn = sqlite3.connect(self.progress_db_path)
        cursor = conn.cursor()
        
        try:
            # Standalone review sessions default coordinates to 0
            cursor.execute("""
                INSERT INTO research_activity_log (phase_num, unit_num, lesson_num, activity_type, content_id, is_correct, is_review_item, response_latency_ms)
                VALUES (0, 0, 0, ?, ?, ?, 1, ?)
            """, (activity_type, content_id, 1 if is_correct else 0, latency_ms))

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
                        interval_days = 1 if repetitions == 1 else (6 if repetitions == 2 else int(old_interval * ease_factor))
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
            print(f"❌ Review Tracking Error: {e}")
        finally:
            conn.close()