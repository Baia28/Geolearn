import sqlite3

class PassiveReviewEngine:
    def __init__(self, db_manager):
        self.db = db_manager

    def build_unit_master_sheet(self, phase_num: int, unit_num: int):
        """Builds a structured dictionary of all content within a specific unit."""
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
        conn.close()

        # Data structure: { lesson_num: {'vocab': [], 'pairs': [], 'dialogues': []} }
        master_sheet = {}

        for lesson_id, lesson_num in lessons:
            master_sheet[lesson_num] = {'vocab': [], 'pairs': [], 'dialogues': []}
            raw_steps = self.db.get_lesson_structure(lesson_id)

            for _, comp_type, assoc_id in raw_steps:
                if comp_type == 'monologue':
                    word_data = self.db.get_word_details(assoc_id)
                    if word_data:
                        # (id, geo, eng, trans, image, audio)
                        master_sheet[lesson_num]['vocab'].append({
                            'geo': word_data[1], 'eng': word_data[2], 
                            'trans': word_data[3], 'audio': word_data[5]
                        })
                
                elif comp_type == 'convo_pair':
                    pair_data = self.db.get_convo_pair_details(assoc_id)
                    if pair_data:
                        master_sheet[lesson_num]['pairs'].append(pair_data)
                
                elif comp_type == 'dialogue':
                    lines = self.db.get_dialogue_lines(assoc_id)
                    if lines:
                        master_sheet[lesson_num]['dialogues'].append(lines)

        return master_sheet