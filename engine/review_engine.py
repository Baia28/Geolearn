# (The Maintainer): This handles your long-term memory (the Spaced Repetition System). 
# It talks directly to db_managers.py to pull a flat list of cards that are due 
# for review today based on their SRS intervals.

import sqlite3
import random
import os
import datetime
import time

class ReviewSession:
    def __init__(self, db_name="content_poolbook.db", phase_num=None, unit_num=None, max_items=12):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.project_root, "database", db_name)
        self.progress_db_path = os.path.join(self.project_root, "database", "user_progress.db")

        self.phase_num = phase_num
        self.unit_num = unit_num
        self.max_items = max_items
        self.queue = []
        self.total_exercises = 0
        self.completed_count = 0
        
        self._ensure_progress_schema()
        self._build_review_session()

    def _ensure_progress_schema(self):
        """Ensures research_activity_log table and required columns exist."""
        try:
            conn = sqlite3.connect(self.progress_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_activity_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phase_num INTEGER,
                    unit_num INTEGER,
                    lesson_num INTEGER,
                    activity_type TEXT,
                    content_id INTEGER,
                    is_correct INTEGER,
                    is_review_item INTEGER,
                    response_latency_ms INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("PRAGMA table_info(research_activity_log)")
            existing_cols = [row[1] for row in cursor.fetchall()]
            
            if "activity_type" not in existing_cols:
                cursor.execute("ALTER TABLE research_activity_log ADD COLUMN activity_type TEXT")
            if "response_latency_ms" not in existing_cols:
                cursor.execute("ALTER TABLE research_activity_log ADD COLUMN response_latency_ms INTEGER")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Progress DB Schema migration warning: {e}")

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
        """Fetches review items using clean two-step queries to avoid SQLite attach locks."""
        unit_content_ids = None

        # 1. Fetch content IDs for unit review from content_poolbook.db
        if self.phase_num is not None and self.unit_num is not None:
            try:
                conn_content = sqlite3.connect(self.db_path)
                cursor_content = conn_content.cursor()

                # Dynamic column check on units and lessons tables
                cursor_content.execute("PRAGMA table_info(units)")
                unit_cols = [row[1] for row in cursor_content.fetchall()]
                cursor_content.execute("PRAGMA table_info(lessons)")
                lesson_cols = [row[1] for row in cursor_content.fetchall()]

                unit_col = "unit_num" if "unit_num" in unit_cols else ("unit_id" if "unit_id" in unit_cols else None)
                phase_col = "phase_num" if "phase_num" in unit_cols else ("phase_id" if "phase_id" in unit_cols else None)

                if unit_col and phase_col:
                    cursor_content.execute(f"""
                        SELECT DISTINCT lc.associated_id 
                        FROM lesson_contents lc
                        JOIN lessons l ON lc.lesson_id = l.lesson_id
                        JOIN units u ON l.unit_id = u.unit_id
                        WHERE u.{unit_col} = ? AND u.{phase_col} = ?
                    """, (self.unit_num, self.phase_num))
                elif "unit_num" in lesson_cols and "phase_num" in lesson_cols:
                    cursor_content.execute("""
                        SELECT DISTINCT lc.associated_id 
                        FROM lesson_contents lc
                        JOIN lessons l ON lc.lesson_id = l.lesson_id
                        WHERE l.unit_num = ? AND l.phase_num = ?
                    """, (self.unit_num, self.phase_num))
                else:
                    cursor_content.execute("""
                        SELECT DISTINCT lc.associated_id 
                        FROM lesson_contents lc
                        JOIN lessons l ON lc.lesson_id = l.lesson_id
                        WHERE l.unit_id = ?
                    """, (self.unit_num,))

                unit_content_ids = [row[0] for row in cursor_content.fetchall() if row[0] is not None]
                conn_content.close()
            except Exception as e:
                print(f"⚠️ Error fetching unit content IDs: {e}")
                unit_content_ids = []

            if not unit_content_ids:
                return []

        # 2. Query user_progress.db for SRS priorities
        conn_prog = sqlite3.connect(self.progress_db_path)
        cursor_prog = conn_prog.cursor()
        today_str = datetime.date.today().isoformat()
        
        review_ids = []
        try:
            if unit_content_ids is not None:
                placeholders = ",".join(["?"] * len(unit_content_ids))
                cursor_prog.execute(f"""
                    SELECT content_id FROM srs_registry 
                    WHERE content_id IN ({placeholders})
                    ORDER BY next_review_date ASC, ease_factor ASC
                    LIMIT ?
                """, unit_content_ids + [limit])
                review_ids = [row[0] for row in cursor_prog.fetchall()]

                # Backfill with remaining unit words if SRS queue has fewer than limit
                if len(review_ids) < limit:
                    needed = limit - len(review_ids)
                    remaining = [cid for cid in unit_content_ids if cid not in review_ids]
                    random.shuffle(remaining)
                    review_ids.extend(remaining[:needed])
            else:
                # Global Quick Review
                cursor_prog.execute("""
                    SELECT content_id FROM srs_registry 
                    WHERE next_review_date <= ? 
                    ORDER BY ease_factor ASC, mastery_level ASC 
                    LIMIT ?
                """, (today_str, limit))
                review_ids = [row[0] for row in cursor_prog.fetchall()]
                
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
                    cursor_prog.execute(query, params)
                    review_ids.extend([row[0] for row in cursor_prog.fetchall()])
        except Exception as e:
            print(f"⚠️ Error querying SRS registry: {e}")
            if unit_content_ids:
                random.shuffle(unit_content_ids)
                review_ids = unit_content_ids[:limit]
        finally:
            conn_prog.close()

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

        from engine.db_managers import ContentDBManager
        db_mgr = ContentDBManager(self.db_path)
        
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

            # Fetch audio path from media table
            audio_file = db_mgr.get_content_audio_path(c_id)

            word_data = {
                "id": c_id, 
                "eng": eng, 
                "geo": geo, 
                "trans": display_trans,
                "audio": audio_file  # e.g., 'audio/gamarjoba.m4a'
            }
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

    def submit_answer(self, is_correct, user_input=None):
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