import sqlite3
from typing import List, Dict, Any

class AlphabetDB:
    """Handles SQLite operations for the Georgian Alphabet hub using content_poolbook.db schema."""
    
    def __init__(self, db_path: str = "database/content_poolbook.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_alphabet_letters(self) -> List[Dict[str, Any]]:
        """Fetches all 33 Mkhedruli letters with letter sound paths and example image paths."""
        query = """
            SELECT 
                c.content_id, 
                c.georgian, 
                c.transliteration, 
                c.english AS linguistic_desc,
                m_l_aud.file_path AS letter_audio,
                m_v_img.file_path AS example_image
            FROM content c
            JOIN types t ON c.type_id = t.type_id
            JOIN content_tags ct ON c.content_id = ct.content_id
            JOIN tags tg ON ct.tag_id = tg.tag_id
            LEFT JOIN media m_l_aud ON c.content_id = m_l_aud.content_id 
                AND m_l_aud.media_type_id = (SELECT media_type_id FROM media_types WHERE name = 'audio_f_default')
            LEFT JOIN convo_pairs cp ON c.content_id = cp.prompt_content_id
            LEFT JOIN content v ON cp.response_content_id = v.content_id
            LEFT JOIN media m_v_img ON v.content_id = m_v_img.content_id 
                AND m_v_img.media_type_id = (SELECT media_type_id FROM media_types WHERE name = 'image')
            WHERE t.name = 'letter' AND tg.name = 'alphabet'
            ORDER BY c.content_id ASC;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
            return [dict(row) for row in rows]

    def get_letter_detail_by_index(self, index: int) -> Dict[str, Any]:
        """Fetches detailed information and example word data for a letter by its 0-indexed position."""
        letters = self.get_alphabet_letters()
        if not letters or index < 0 or index >= len(letters):
            return {"letter": None, "example": None, "index": 0, "total": 0}
        
        target_letter = letters[index]

        example_query = """
            SELECT 
                c.georgian AS word, 
                c.english AS meaning, 
                c.transliteration,
                m_img.file_path AS image, 
                m_aud.file_path AS audio
            FROM convo_pairs cp
            JOIN content c ON cp.response_content_id = c.content_id
            LEFT JOIN media m_img ON c.content_id = m_img.content_id 
                AND m_img.media_type_id = (SELECT media_type_id FROM media_types WHERE name = 'image')
            LEFT JOIN media m_aud ON c.content_id = m_aud.content_id 
                AND m_aud.media_type_id = (SELECT media_type_id FROM media_types WHERE name = 'audio_f_default')
            WHERE cp.prompt_content_id = ?;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            example_row = cursor.execute(example_query, (target_letter["content_id"],)).fetchone()
            example_data = dict(example_row) if example_row else None
            
            return {
                "letter": target_letter,
                "example": example_data,
                "index": index,
                "total": len(letters)
            }

    def get_anban_game_questions(self) -> List[Dict[str, Any]]:
        """Queries game items strictly where topic='alphabet' to isolate distractor pools."""
        query = """
            SELECT 
                l.content_id AS letter_id,
                l.georgian AS correct_geo,
                l.transliteration AS letter_trans,
                m_l_aud.file_path AS letter_audio,
                v.georgian AS example_word,
                v.english AS example_meaning,
                m_v_img.file_path AS example_image,
                m_v_aud.file_path AS example_audio
            FROM content l
            JOIN types t_l ON l.type_id = t_l.type_id
            JOIN content_tags ct_l ON l.content_id = ct_l.content_id
            JOIN tags tg_l ON ct_l.tag_id = tg_l.tag_id AND tg_l.name = 'alphabet'
            LEFT JOIN media m_l_aud ON l.content_id = m_l_aud.content_id 
                AND m_l_aud.media_type_id = (SELECT media_type_id FROM media_types WHERE name = 'audio_f_default')
            JOIN convo_pairs cp ON l.content_id = cp.prompt_content_id
            JOIN content v ON cp.response_content_id = v.content_id
            LEFT JOIN media m_v_img ON v.content_id = m_v_img.content_id 
                AND m_v_img.media_type_id = (SELECT media_type_id FROM media_types WHERE name = 'image')
            LEFT JOIN media m_v_aud ON v.content_id = m_v_aud.content_id 
                AND m_v_aud.media_type_id = (SELECT media_type_id FROM media_types WHERE name = 'audio_f_default')
            WHERE t_l.name = 'letter' AND m_v_img.file_path IS NOT NULL;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
            return [dict(row) for row in rows]