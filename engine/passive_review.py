"""Build read-only vocabulary, phrase, pair, and dialogue review sheets."""

import sqlite3

class PassiveReviewEngine:
    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def _empty_lesson_entry(locked: bool = False) -> dict:
        """Create one review section without exposing locked lesson content."""
        return {
            'vocab': [],
            'phrases': [],
            'pairs': [],
            'dialogues': [],
            'category_counts': {'vocab': 0, 'phrases': 0, 'dialogues': 0},
            'locked': locked,
        }

    @staticmethod
    def _lesson_category_counts(cursor, raw_steps: list) -> dict[str, int]:
        """Count category availability without loading locked lesson material."""
        counts = {'vocab': 0, 'phrases': 0, 'dialogues': 0}
        for _, comp_type, assoc_id in raw_steps:
            if comp_type == 'monologue':
                cursor.execute("""
                    SELECT t.name
                    FROM content c
                    JOIN types t ON c.type_id = t.type_id
                    WHERE c.content_id = ?
                """, (assoc_id,))
                row = cursor.fetchone()
                if row:
                    category = 'phrases' if row[0].lower() == 'phrase' else 'vocab'
                    counts[category] += 1
            elif comp_type == 'convo_pair':
                counts['phrases'] += 1
            elif comp_type == 'dialogue':
                counts['dialogues'] += 1
        return counts

    def _populate_lesson_content(
        self,
        cursor,
        raw_steps: list,
        entry: dict,
    ) -> None:
        """Add one unlocked lesson's reference material to its review section."""
        for _, comp_type, assoc_id in raw_steps:
            if comp_type == 'monologue':
                cursor.execute("""
                    SELECT t.name
                    FROM content c
                    JOIN types t ON c.type_id = t.type_id
                    WHERE c.content_id = ?
                """, (assoc_id,))
                type_res = cursor.fetchone()
                db_content_type = type_res[0].lower() if type_res else 'word'

                word_data = self.db.get_word_details(assoc_id)
                if word_data:
                    item = {
                        'geo': word_data[1], 'eng': word_data[2],
                        'trans': word_data[3], 'audio': word_data[5],
                    }
                    if db_content_type == 'phrase':
                        entry['phrases'].append(item)
                    else:
                        entry['vocab'].append(item)

            elif comp_type == 'convo_pair':
                pair_data = self.db.get_convo_pair_details(assoc_id)
                if pair_data:
                    entry['pairs'].append(pair_data)

            elif comp_type == 'dialogue':
                lines = self.db.get_dialogue_lines(assoc_id)
                if lines:
                    entry['dialogues'].append(lines)

    def build_unit_master_sheet(
        self,
        phase_num: int,
        unit_num: int,
        accessible_lesson_ids: list[int],
    ):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                l.lesson_id,
                l.sequence_order,
                l.title,
                p.title,
                u.title
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            WHERE p.sequence_order = ? AND u.sequence_order = ?
            ORDER BY l.sequence_order ASC
        """, (phase_num, unit_num))
        lessons = cursor.fetchall()

        master_sheet = {}

        accessible_ids = set(accessible_lesson_ids)
        for lesson_id, lesson_num, lesson_title, phase_title, unit_title in lessons:
            entry = self._empty_lesson_entry(locked=lesson_id not in accessible_ids)
            raw_steps = self.db.get_lesson_structure(lesson_id)
            entry.update({
                'lesson_id': lesson_id,
                'phase_num': phase_num,
                'phase_title': phase_title,
                'unit_num': unit_num,
                'unit_title': unit_title,
                'lesson_num': lesson_num,
                'lesson_title': lesson_title,
                'category_counts': self._lesson_category_counts(cursor, raw_steps),
            })
            if not entry['locked']:
                self._populate_lesson_content(cursor, raw_steps, entry)
            master_sheet[lesson_num] = entry

        conn.close()
        return master_sheet

    def build_global_master_sheet(self, accessible_lesson_ids: list[int]):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                l.lesson_id,
                p.sequence_order,
                p.title,
                u.sequence_order,
                u.title,
                l.sequence_order,
                l.title
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            ORDER BY p.sequence_order, u.sequence_order, l.sequence_order ASC
        """)
        lessons = cursor.fetchall()
        accessible_ids = set(accessible_lesson_ids)

        master_sheet = {}

        for (
            lesson_id,
            phase_num,
            phase_title,
            unit_num,
            unit_title,
            lesson_num,
            lesson_title,
        ) in lessons:
            label = f"Phase {phase_num} • Unit {unit_num} • Lesson {lesson_num}"
            entry = self._empty_lesson_entry(locked=lesson_id not in accessible_ids)
            raw_steps = self.db.get_lesson_structure(lesson_id)
            entry.update({
                'lesson_id': lesson_id,
                'phase_num': phase_num,
                'phase_title': phase_title,
                'unit_num': unit_num,
                'unit_title': unit_title,
                'lesson_num': lesson_num,
                'lesson_title': lesson_title,
                'category_counts': self._lesson_category_counts(cursor, raw_steps),
            })
            if not entry['locked']:
                self._populate_lesson_content(cursor, raw_steps, entry)
            master_sheet[label] = entry
        
        conn.close()
        return master_sheet
