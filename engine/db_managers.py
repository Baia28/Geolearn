# engine/db_managers.py: The Gatekeeper. 
# It handles all SQLite queries, SRS interval math, 
# and database connections.

import sqlite3
import os
import datetime
import random

class ProgressDBManager:
    def __init__(self, db_name="user_progress.db"):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.project_root, "database", db_name)
        self._activity_id_cache = {}

    def _get_activity_id(self, activity_code):
        """Translates a string like 'mc_geo_to_eng' into its integer foreign key."""
        if activity_code in self._activity_id_cache:
            return self._activity_id_cache[activity_code]
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT activity_id FROM activity_types WHERE activity_code = ?", (activity_code,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            self._activity_id_cache[activity_code] = result[0]
            return result[0]
        else:
            print(f"⚠️ Warning: Activity code '{activity_code}' not found in database.")
            return None

    def log_user_response(self, phase_num, unit_num, lesson_num, activity_code, content_id, is_correct, is_review, latency_ms, user_input=None):
        """Logs interaction telemetry and coordinates the Spaced Repetition (SRS) update."""
        activity_id = self._get_activity_id(activity_code)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO research_activity_log 
                (phase_num, unit_num, lesson_num, activity_id, content_id, user_input, is_correct, is_review_item, response_latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (phase_num, unit_num, lesson_num, activity_id, content_id, user_input, 1 if is_correct else 0, 1 if is_review else 0, latency_ms))

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
                            # Maintain the interval for inline lesson reviews
                            interval_days = max(1, old_interval)
                    else:
                        repetitions = 0
                        interval_days = 0
                        ease_factor = max(1.3, old_ef - 0.2)
                    
                interval_days = min(120, interval_days)
                next_date = (datetime.date.today() + datetime.timedelta(days=interval_days)).isoformat()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO srs_registry 
                    (content_id, mastery_level, ease_factor, repetitions, interval_days, next_review_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (content_id, repetitions, ease_factor, repetitions, interval_days, next_date))
                
            conn.commit()
        except Exception as e:
            print(f"❌ DBManager Logging Error: {e}")
        finally:
            conn.close()

    def mark_lesson_completed(self, lesson_id):
        """Commits full lesson milestone clearances to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO lesson_progress (lesson_id, is_completed, last_accessed)
                VALUES (?, 1, CURRENT_TIMESTAMP)
            """, (lesson_id,))
            conn.commit()
        except Exception as e:
            print(f"❌ Progress Log Error: {e}")
        finally:
            conn.close()
            
    def register_pruned_card_to_srs(self, content_id):
        """Forces bypassed/pruned alternative-direction cards straight to SRS review database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            today_str = datetime.date.today().isoformat()
            cursor.execute("""
                INSERT OR IGNORE INTO srs_registry 
                (content_id, mastery_level, ease_factor, repetitions, interval_days, next_review_date)
                VALUES (?, 0, 2.5, 0, 0, ?)
            """, (content_id, today_str))
            conn.commit()
        except Exception as e:
            print(f"⚠️ SRS registration failed: {e}")
        finally:
            conn.close()

    def get_urgent_review_items(self, limit=3):
        """Fetches top overdue SRS review items."""
        conn = sqlite3.connect(self.db_path)
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

    def get_completed_lesson_ids(self):
        """Gathers a flat list of all completed lesson IDs for automated routing lookup."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT lesson_id FROM lesson_progress WHERE is_completed = 1")
            completed = [row[0] for row in cursor.fetchall()]
        except Exception:
            completed = []
        finally:
            conn.close()
        return completed

    def should_fade_transliteration(self, content_id, mastery_threshold=3):
        """Checks if the user has mastered a word enough times to hide its phonetics helper."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT repetitions FROM srs_registry WHERE content_id = ?", (content_id,))
            res = cursor.fetchone()
            if res and res[0] >= mastery_threshold:
                return True
        except Exception:
            pass
        finally:
            conn.close()
        return False

    def get_last_production_activity_code(self, content_id):
        """
        Queries historical telemetry to see which production mode (typing or audio)
        the user was exposed to most recently.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT at.activity_code 
                FROM research_activity_log ral
                JOIN activity_types at ON ral.activity_id = at.activity_id
                WHERE ral.content_id = ? AND at.activity_code IN ('type_georgian', 'audio_dictation')
                ORDER BY ral.timestamp DESC LIMIT 1
            """, (content_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception:
            return None
        finally:
            conn.close()



#####################################################################################################



class ContentDBManager:
    def __init__(self, db_name="content_poolbook.db"):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.project_root, "database", db_name)

    def resolve_lesson_id(self, phase_num, unit_num, lesson_num):
        """Converts user sequence coordinates into the primary key lesson_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.lesson_id 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            WHERE p.sequence_order = ? AND u.sequence_order = ? AND l.sequence_order = ?
        """, (phase_num, unit_num, lesson_num))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None

    def get_lesson_structure(self, lesson_id):
        """Fetches chronological step structure for building study sessions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT lc.step_order, lct.name, lc.associated_id
            FROM lesson_contents lc
            JOIN lesson_component_types lct ON lc.component_type_id = lct.component_type_id
            WHERE lc.lesson_id = ?
            ORDER BY lc.step_order ASC
        """, (lesson_id,))
        res = cursor.fetchall()
        conn.close()
        return res

    def get_word_details(self, content_id):
        """Fetches details for a target word along with image and audio file paths from relational media tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                c.content_id, 
                c.georgian, 
                c.english, 
                c.transliteration,
                (SELECT m.file_path 
                 FROM media m 
                 JOIN media_types mt ON m.media_type_id = mt.media_type_id 
                 WHERE m.content_id = c.content_id AND LOWER(mt.name) = 'image' LIMIT 1) AS image,
                (SELECT m.file_path 
                 FROM media m 
                 JOIN media_types mt ON m.media_type_id = mt.media_type_id 
                 WHERE m.content_id = c.content_id AND LOWER(mt.name) = 'audio' LIMIT 1) AS audio
            FROM content c
            WHERE c.content_id = ?
        """, (content_id,))

        res = cursor.fetchone()
        conn.close()
        return res  # Returns: (content_id, georgian, english, transliteration, image_path, audio_path)

    def get_convo_pair_details(self, pair_id):
        """Fetches matched conversational components with support for multiple correct responses."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. Resolve prompt_content_id (pair_id might be a rowid or a content_id)
            cursor.execute("""
                SELECT prompt_content_id FROM convo_pairs 
                WHERE rowid = ? OR prompt_content_id = ? 
                LIMIT 1
            """, (pair_id, pair_id))
            prompt_res = cursor.fetchone()
            
            if not prompt_res:
                return None
            
            prompt_content_id = prompt_res[0]

            # 2. Fetch prompt details
            cursor.execute("SELECT georgian, english FROM content WHERE content_id = ?", (prompt_content_id,))
            prompt_row = cursor.fetchone()
            if not prompt_row:
                return None

            # 3. Fetch ALL valid responses linked to this prompt
            cursor.execute("""
                SELECT c.content_id, c.georgian, c.english 
                FROM convo_pairs cp
                JOIN content c ON cp.response_content_id = c.content_id
                WHERE cp.prompt_content_id = ?
            """, (prompt_content_id,))
            valid_responses = cursor.fetchall()
            
            if not valid_responses:
                return None

            # 4. Pick ONE valid response at random for this exercise instance
            selected_correct_response = random.choice(valid_responses)
            all_valid_response_ids = tuple(r[0] for r in valid_responses)

            # 5. Fetch 2 distractors that are NOT valid responses for this prompt
            placeholders = ','.join('?' * len(all_valid_response_ids))
            distractor_query = f"""
                SELECT georgian, english 
                FROM content 
                WHERE content_id NOT IN ({placeholders}) 
                AND type_id = (SELECT type_id FROM types WHERE name='phrase')
                ORDER BY RANDOM() LIMIT 2
            """
            cursor.execute(distractor_query, all_valid_response_ids)
            distractors = cursor.fetchall()

            return {
                'prompt': {'georgian': prompt_row[0], 'english': prompt_row[1]},
                'correct_response': {'georgian': selected_correct_response[1], 'english': selected_correct_response[2]},
                'all_valid_responses': [r[1] for r in valid_responses],
                'distractors': [{'georgian': d[0], 'english': d[1]} for d in distractors]
            }
        finally:
            conn.close()

    def get_dialogue_details(self, dialogue_id):
        """Fetches dialogue metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT dialogue_id, internal_code FROM dialogues WHERE dialogue_id = ?", (dialogue_id,))
        res = cursor.fetchone()
        conn.close()
        return res

    def get_dialogue_lines(self, dialogue_id):
        """Fetches lines in alphabetical / order sequence for a targeted dialogue block."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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

    def get_distractors(self, lesson_id, correct_content_id, limit=2):
        """Dynamically generates contextual word distractors across tiers."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        distractors = []
        
        # Tier 1: Same Lesson
        if lesson_id:
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

        # Tier 2: Same Unit Fallback
        if len(distractors) < limit and lesson_id:
            needed = limit - len(distractors)
            picked_english = [row[0] for row in distractors]
            
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

        # Tier 3: Global Dictionary Fallback
        if len(distractors) < limit:
            needed = limit - len(distractors)
            picked_english = [row[0] for row in distractors]
            
            query = """
                SELECT DISTINCT english, georgian FROM content 
                WHERE content_id != ? AND LENGTH(english) >= 2
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
        return distractors[:limit]

    def get_convo_distractors(self, lesson_id, correct_response_id, limit=2):
        """Pulls contextual conversational response alternatives."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        distractors = []
        
        # Tier 1: Same Unit with 'response' tags
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
        
        # Tier 2: Global conversational alternatives fallback
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
            
        conn.close()
        return distractors[:limit]



    def get_convo_pair_for_lesson(self, lesson_id, distractor_limit=3):
        """Fetches a conversation pair for a lesson and uses context-aware distractors."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Fetch a target conversational pair for this specific lesson
        query = """
            SELECT 
                p.georgian AS prompt_geo,
                p.transliteration AS prompt_trans,
                r.georgian AS correct_geo,
                cp.response_content_id
            FROM convo_pairs cp
            JOIN content p ON cp.prompt_content_id = p.content_id
            JOIN content r ON cp.response_content_id = r.content_id
            JOIN lesson_contents lc ON cp.prompt_content_id = lc.associated_id
            WHERE lc.lesson_id = ?
            ORDER BY RANDOM() LIMIT 1;
        """
        cursor.execute(query, (lesson_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None, []

        prompt_geo, prompt_trans, correct_geo, response_id = row

        target_data = {
            "prompt_geo": prompt_geo,
            "prompt_trans": prompt_trans,
            "correct_geo": correct_geo
        }

        # 2. Leverage your SMART distractor function!
        raw_distractors = self.get_convo_distractors(lesson_id, response_id, limit=distractor_limit)
        
        # get_convo_distractors returns tuples (georgian, english); extract just the Georgian strings
        distractors = [d[0] for d in raw_distractors]

        return target_data, distractors



    def find_next_incomplete_lesson_coordinates(self, completed_ids):
        """Scans the curriculum to find sequence orders for the next incomplete lesson."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.lesson_id, p.sequence_order, u.sequence_order, l.sequence_order 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            ORDER BY p.sequence_order ASC, u.sequence_order ASC, l.sequence_order ASC
        """)
        all_lessons = cursor.fetchall()
        conn.close()

        for lesson_id, p_num, u_num, l_num in all_lessons:
            if lesson_id not in completed_ids:
                return lesson_id, p_num, u_num, l_num

        # Absolute fallback if everything has been completed
        if all_lessons:
            return all_lessons[0][0], all_lessons[0][1], all_lessons[0][2], all_lessons[0][3]
        return 1, 1, 1, 1
    


    # =========================================================================
    # CURRICULUM & PROGRESS NAVIGATION QUERIES
    # =========================================================================

    def get_phases_summary(self, completed_lesson_ids: list):
        """
        Fetches all phases along with their total lesson counts, completed lesson counts,
        and progress ratios.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.sequence_order, p.title, l.lesson_id
            FROM phases p
            LEFT JOIN units u ON p.phase_id = u.phase_id
            LEFT JOIN lessons l ON u.unit_id = l.unit_id
            ORDER BY p.sequence_order ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        phases_map = {}
        completed_set = set(completed_lesson_ids)

        for phase_num, phase_title, lesson_id in rows:
            if phase_num not in phases_map:
                phases_map[phase_num] = {
                    "phase_num": phase_num,
                    "title": phase_title or f"Phase {phase_num}",
                    "total_lessons": 0,
                    "completed_lessons": 0,
                    "progress": 0.0
                }
            
            if lesson_id is not None:
                phases_map[phase_num]["total_lessons"] += 1
                if lesson_id in completed_set:
                    phases_map[phase_num]["completed_lessons"] += 1

        summary_list = []
        for phase_num in sorted(phases_map.keys()):
            p_data = phases_map[phase_num]
            total = p_data["total_lessons"]
            p_data["progress"] = (p_data["completed_lessons"] / total) if total > 0 else 0.0
            summary_list.append(p_data)

        return summary_list

    def get_units_for_phase(self, phase_num: int, completed_lesson_ids: list):
        """
        Fetches all units inside a given phase with progress ratios.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.sequence_order, u.title, l.lesson_id
            FROM units u
            JOIN phases p ON u.phase_id = p.phase_id
            LEFT JOIN lessons l ON u.unit_id = l.unit_id
            WHERE p.sequence_order = ?
            ORDER BY u.sequence_order ASC
        """, (phase_num,))
        rows = cursor.fetchall()
        conn.close()

        units_map = {}
        completed_set = set(completed_lesson_ids)

        for unit_num, unit_title, lesson_id in rows:
            if unit_num not in units_map:
                units_map[unit_num] = {
                    "unit_num": unit_num,
                    "title": unit_title or f"Unit {unit_num}",
                    "total_lessons": 0,
                    "completed_lessons": 0,
                    "progress": 0.0
                }
            
            if lesson_id is not None:
                units_map[unit_num]["total_lessons"] += 1
                if lesson_id in completed_set:
                    units_map[unit_num]["completed_lessons"] += 1

        summary_list = []
        for unit_num in sorted(units_map.keys()):
            u_data = units_map[unit_num]
            total = u_data["total_lessons"]
            u_data["progress"] = (u_data["completed_lessons"] / total) if total > 0 else 0.0
            summary_list.append(u_data)

        return summary_list

    def get_lessons_for_unit(self, phase_num: int, unit_num: int, completed_lesson_ids: list):
        """
        Fetches all individual lessons inside a unit.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l.lesson_id, l.sequence_order, l.title
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            WHERE p.sequence_order = ? AND u.sequence_order = ?
            ORDER BY l.sequence_order ASC
        """, (phase_num, unit_num))
        rows = cursor.fetchall()
        conn.close()

        completed_set = set(completed_lesson_ids)
        lesson_list = []

        for lesson_id, lesson_num, lesson_title in rows:
            is_completed = lesson_id in completed_set
            lesson_list.append({
                "lesson_id": lesson_id,
                "lesson_num": lesson_num,
                "title": lesson_title or f"Lesson {lesson_num}",
                "is_completed": is_completed
            })

        return lesson_list