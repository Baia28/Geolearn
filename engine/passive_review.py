import sqlite3

class PassiveReviewEngine:
    def __init__(self, db_manager):
        self.db = db_manager

    def build_unit_master_sheet(self, phase_num: int, unit_num: int):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # 1. Fetch all lessons for this Phase and Unit
        cursor.execute("""
            SELECT l.lesson_id, l.sequence_order 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            WHERE p.sequence_order = ? AND u.sequence_order = ?
            ORDER BY l.sequence_order ASC
        """, (phase_num, unit_num))
        lessons = cursor.fetchall()

        # Data structure initialization
        master_sheet = {}

        for lesson_id, lesson_num in lessons:
            master_sheet[lesson_num] = {'vocab': [], 'phrases': [], 'pairs': [], 'dialogues': []}
            raw_steps = self.db.get_lesson_structure(lesson_id)

            for _, comp_type, assoc_id in raw_steps:
                if comp_type == 'monologue':
                    # Explicitly check the database 'type' (word vs phrase)
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
                            'trans': word_data[3], 'audio': word_data[5]
                        }
                        # Route based on the exact database type mapping
                        if db_content_type == 'phrase':
                            master_sheet[lesson_num]['phrases'].append(item)
                        else:
                            master_sheet[lesson_num]['vocab'].append(item)
                
                elif comp_type == 'convo_pair':
                    pair_data = self.db.get_convo_pair_details(assoc_id)
                    if pair_data:
                        master_sheet[lesson_num]['pairs'].append(pair_data)
                
                elif comp_type == 'dialogue':
                    lines = self.db.get_dialogue_lines(assoc_id)
                    if lines:
                        master_sheet[lesson_num]['dialogues'].append(lines)

        conn.close()
        return master_sheet

    def build_global_master_sheet(self, completed_lesson_ids: list):
        if not completed_lesson_ids:
            return {}

        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        placeholders = ",".join("?" * len(completed_lesson_ids))
        cursor.execute(f"""
            SELECT l.lesson_id, p.sequence_order, u.sequence_order, l.sequence_order 
            FROM lessons l
            JOIN units u ON l.unit_id = u.unit_id
            JOIN phases p ON u.phase_id = p.phase_id
            WHERE l.lesson_id IN ({placeholders})
            ORDER BY p.sequence_order, u.sequence_order, l.sequence_order ASC
        """, completed_lesson_ids)
        lessons = cursor.fetchall()

        master_sheet = {}

        for lesson_id, phase_num, unit_num, lesson_num in lessons:
            # Create a clear global label
            label = f"Phase {phase_num} • Unit {unit_num} • Lesson {lesson_num}"
            master_sheet[label] = {'vocab': [], 'phrases': [], 'pairs': [], 'dialogues': []}
            
            raw_steps = self.db.get_lesson_structure(lesson_id)

            for _, comp_type, assoc_id in raw_steps:
                if comp_type == 'monologue':
                    cursor.execute("""
                        SELECT t.name FROM content c
                        JOIN types t ON c.type_id = t.type_id
                        WHERE c.content_id = ?
                    """, (assoc_id,))
                    type_res = cursor.fetchone()
                    db_content_type = type_res[0].lower() if type_res else 'word'

                    word_data = self.db.get_word_details(assoc_id)
                    if word_data:
                        item = {'geo': word_data[1], 'eng': word_data[2], 'trans': word_data[3], 'audio': word_data[5]}
                        if db_content_type == 'phrase':
                            master_sheet[label]['phrases'].append(item)
                        else:
                            master_sheet[label]['vocab'].append(item)
                
                elif comp_type == 'convo_pair':
                    pair_data = self.db.get_convo_pair_details(assoc_id)
                    if pair_data:
                        master_sheet[label]['pairs'].append(pair_data)
                
                elif comp_type == 'dialogue':
                    lines = self.db.get_dialogue_lines(assoc_id)
                    if lines:
                        master_sheet[label]['dialogues'].append(lines)
        
        conn.close()
        # Clean out empty labels before returning
        return {k: v for k, v in master_sheet.items() if any(v.values())}