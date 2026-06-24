import sqlite3
import pandas as pd
import math

# ======================================
# FILE PATHS
# ===============================
DB_PATH = "database/content_poolbook.db"

# if I switch to CSV..
#CSV_CONTENT = "content_master (1).xlsx - Content_Master.csv"
#CSV_DIALOGUES = "content_master (1).xlsx - Dialogues.csv"
#CSV_LESSONS = "content_master (1).xlsx - Lessons.csv"

# ==================================
# HELPER FUNCTIONS
# ===========================
def clean_str(val):
    """Safely handle Pandas NaN values and strip whitespace."""
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip()
    return s if s else None

def get_or_create_tag(cursor, tag_name, group_name):
    """Finds a tag by name and group. Creates it if missing."""
    tag_name = clean_str(tag_name)
    if not tag_name:
        return None
        
    tag_name = tag_name.lower()
    
    # Get group_id
    cursor.execute("SELECT group_id FROM tag_groups WHERE name=?", (group_name,))
    group_row = cursor.fetchone()
    if not group_row:
        return None
    group_id = group_row[0]
    
    # Check if tag exists
    cursor.execute("SELECT tag_id FROM tags WHERE name=? AND group_id=?", (tag_name, group_id))
    tag_row = cursor.fetchone()
    if tag_row:
        return tag_row[0]
        
    # Create tag
    cursor.execute("INSERT INTO tags (name, group_id) VALUES (?, ?)", (tag_name, group_id))
    return cursor.lastrowid

# =========================================
# MAIN EXECUTION
# ====================================
def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Dropping old tables to ensure clean rebuild...")
    tables_to_drop = [
        "lesson_component_types", "lesson_contents", "lessons", "units", "phases", 
        "dialogue_lines", "dialogues", "media", "media_types", 
        "convo_pairs", "content_tags", "content", 
        "tags", "tag_groups", "types"
    ]
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")

    print("Building schema...")
    
    # --- 1. SCHEMA DEFINITION ---
    cursor.executescript("""
    CREATE TABLE types (
        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE tag_groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE tags (
        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        name TEXT NOT NULL,
        FOREIGN KEY(group_id) REFERENCES tag_groups(group_id),
        UNIQUE(name, group_id)
    );

    CREATE TABLE content (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_id INTEGER,
        georgian TEXT UNIQUE NOT NULL,
        transliteration TEXT,
        english TEXT NOT NULL,
        difficulty INTEGER DEFAULT 1,
        mastery_weight INTEGER DEFAULT 100,
        notes TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(type_id) REFERENCES types(type_id)
    );

    CREATE TABLE content_tags (
        content_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY(content_id, tag_id),
        FOREIGN KEY(content_id) REFERENCES content(content_id),
        FOREIGN KEY(tag_id) REFERENCES tags(tag_id)
    );
                  
    CREATE TABLE convo_pairs (
    prompt_content_id INTEGER,
    response_content_id INTEGER,
    PRIMARY KEY (prompt_content_id, response_content_id),
    FOREIGN KEY(prompt_content_id) REFERENCES content(content_id),
    FOREIGN KEY(response_content_id) REFERENCES content(content_id)
    );                     

    CREATE TABLE media_types (
        media_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE media (
        media_id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER,
        media_type_id INTEGER,
        file_path TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY(content_id) REFERENCES content(content_id),
        FOREIGN KEY(media_type_id) REFERENCES media_types(media_type_id)
    );

    CREATE TABLE dialogues (
        dialogue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        internal_code TEXT UNIQUE NOT NULL,
        topic_tag_id INTEGER,
        description TEXT,
        active INTEGER DEFAULT 1,
        FOREIGN KEY(topic_tag_id) REFERENCES tags(tag_id)
    );

    CREATE TABLE dialogue_lines (
        line_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dialogue_id INTEGER,
        line_order INTEGER,
        speaker TEXT,
        content_id INTEGER,
        audio_override_path TEXT,
        FOREIGN KEY(dialogue_id) REFERENCES dialogues(dialogue_id),
        FOREIGN KEY(content_id) REFERENCES content(content_id)
    );

    CREATE TABLE phases (
        phase_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sequence_order INTEGER NOT NULL,
        title TEXT UNIQUE NOT NULL
    );

    CREATE TABLE units (
        unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        phase_id INTEGER,
        sequence_order INTEGER NOT NULL,
        title TEXT NOT NULL,
        FOREIGN KEY(phase_id) REFERENCES phases(phase_id)
    );

    CREATE TABLE lessons (
        lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_id INTEGER,
        sequence_order INTEGER NOT NULL,
        title TEXT NOT NULL,
        FOREIGN KEY(unit_id) REFERENCES units(unit_id)
    );

    CREATE TABLE lesson_component_types (
        component_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL 
    );

    CREATE TABLE lesson_contents (
        lesson_id INTEGER,
        component_type_id INTEGER,
        associated_id INTEGER, 
        PRIMARY KEY (lesson_id, component_type_id, associated_id),
        FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id),
        FOREIGN KEY(component_type_id) REFERENCES lesson_component_types(component_type_id)
    );
                         
    """)

    # --- 2. PRE-POPULATE STATIC TABLES ---
    cursor.executescript("""
    INSERT INTO types (name) VALUES ('vocab'), ('pattern'), ('phrase');
    INSERT INTO tag_groups (name) VALUES ('topic'), ('semantic_group'), ('grammar'), ('frequency'), ('level');
    INSERT INTO media_types (name) VALUES ('image'), ('audio_f_default'), ('audio_f_slow'), ('audio_m_default'), ('audio_m_slow');
    INSERT INTO lesson_component_types (name) VALUES ('monologue'), ('dialogue');
    """)
    conn.commit()

    # --- 3. LOAD DATA (Pandas) ---

    print("Loading Master Sheets")
    df_content = pd.read_excel("data/master_sheets.xlsx", sheet_name="Content_Master")
    df_dialogues = pd.read_excel("data/master_sheets.xlsx", sheet_name="Dialogues")
    df_lessons = pd.read_excel("data/master_sheets.xlsx", sheet_name="Lessons")

    #print("Loading CSVs...")
    #df_content = pd.read_csv(CSV_CONTENT)
    #df_dialogues = pd.read_csv(CSV_DIALOGUES)
    #df_lessons = pd.read_csv(CSV_LESSONS)

    # --- 4. IMPORT CONTENT (Pass 1: Content & Tags) ---
    print("Importing Content_Master (Pass 1)...")
    for _, row in df_content.iterrows():
        georgian = clean_str(row.get('Georgian'))
        if not georgian: continue
        
        # Type ID
        type_name = clean_str(row.get('Type'))
        cursor.execute("SELECT type_id FROM types WHERE name=?", (type_name,))
        type_res = cursor.fetchone()
        type_id = type_res[0] if type_res else None

        # Insert Content
        english = clean_str(row.get('English')) or ""
        translit = clean_str(row.get('Transliteration'))
        diff = clean_str(row.get('Difficulty'))
        weight = clean_str(row.get('Weight'))
        diff = int(diff) if diff and diff.isdigit() else 1
        weight = int(weight) if weight and weight.isdigit() else 100

        cursor.execute("""
            INSERT OR IGNORE INTO content (type_id, georgian, transliteration, english, difficulty, mastery_weight)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (type_id, georgian, translit, english, diff, weight))
        
        # Get Content ID
        cursor.execute("SELECT content_id FROM content WHERE georgian=?", (georgian,))
        content_id = cursor.fetchone()[0]

        # Handle Tags
        tag_mappings = [
            ('Topic', 'topic'), ('Semantic_Group', 'semantic_group'), 
            ('Grammar', 'grammar'), ('Frequency', 'frequency'), ('Level', 'level')
        ]
        for col_name, group_name in tag_mappings:
            tag_val = clean_str(row.get(col_name))
            if tag_val:
                tag_id = get_or_create_tag(cursor, tag_val, group_name)
                if tag_id:
                    cursor.execute("INSERT OR IGNORE INTO content_tags (content_id, tag_id) VALUES (?, ?)", (content_id, tag_id))

        # Handle Media
        img_path = clean_str(row.get('Image'))
        if img_path:
            cursor.execute("INSERT INTO media (content_id, media_type_id, file_path) VALUES (?, (SELECT media_type_id FROM media_types WHERE name='image'), ?)", (content_id, img_path))
            
    conn.commit()

    # --- 5. IMPORT CONTENT (Pass 2: Conversational Pairs) ---
    print("Importing Conversational Pairs (Pass 2)...")
    for _, row in df_content.iterrows():
        response_geo = clean_str(row.get('Georgian'))
        prompt_geo = clean_str(row.get('Response_To'))
        
        if response_geo and prompt_geo:
            cursor.execute("SELECT content_id FROM content WHERE georgian=?", (response_geo,))
            res_row = cursor.fetchone()
            cursor.execute("SELECT content_id FROM content WHERE georgian=?", (prompt_geo,))
            prompt_row = cursor.fetchone()
            
            if res_row and prompt_row:
                cursor.execute("""
                    INSERT INTO convo_pairs (prompt_content_id, response_content_id) 
                    VALUES (?, ?)
                """, (prompt_row[0], res_row[0]))
    conn.commit()

    # --- 6. IMPORT DIALOGUES ---
    print("Importing Dialogues...")
    for _, row in df_dialogues.iterrows():
        d_name = clean_str(row.get('Dialogue_Name'))
        if not d_name: continue

        topic_tag_id = get_or_create_tag(cursor, clean_str(row.get('Topic')), 'topic')
        desc = clean_str(row.get('Description'))

        # Insert Dialogue Header
        cursor.execute("INSERT OR IGNORE INTO dialogues (internal_code, topic_tag_id, description) VALUES (?, ?, ?)", 
                       (d_name, topic_tag_id, desc))
        
        cursor.execute("SELECT dialogue_id FROM dialogues WHERE internal_code=?", (d_name,))
        d_row = cursor.fetchone()
        if not d_row: continue
        dialogue_id = d_row[0]

        # Insert Line
        order = clean_str(row.get('Order'))
        speaker = clean_str(row.get('Speaker'))
        geo_content = clean_str(row.get('Georgian_Content'))
        audio_over = clean_str(row.get('Audio_Override'))

        cursor.execute("SELECT content_id FROM content WHERE georgian=?", (geo_content,))
        c_row = cursor.fetchone()
        content_id = c_row[0] if c_row else None

        if geo_content and not content_id:
            print(f"  [WARNING] Dialogue line '{geo_content}' not found in Content_Master!")

        cursor.execute("""
            INSERT INTO dialogue_lines (dialogue_id, line_order, speaker, content_id, audio_override_path)
            VALUES (?, ?, ?, ?, ?)
        """, (dialogue_id, order, speaker, content_id, audio_over))
    conn.commit()

    # --- 7. IMPORT LESSONS (AUTOMATED MONOLOGUE/DIALOGUE ENGINE) ---
    print("Importing Lessons into Automated Playlists Architecture...")
    for _, row in df_lessons.iterrows():
        p_num = clean_str(row.get('Phase'))
        p_name = clean_str(row.get('Phase_Name'))
        u_num = clean_str(row.get('Unit'))
        u_name = clean_str(row.get('Unit_Name'))
        l_num = clean_str(row.get('Lesson'))
        c_type = clean_str(row.get('Content_Type')) # 'monologue' or 'dialogue'
        target = clean_str(row.get('Content'))     # The word string or dialogue code (e.g. P1_U1_D1)

        if not p_num or not u_num or not l_num or not c_type or not target: 
            continue

        # Ensure Phase structural hierarchy exists
        cursor.execute("INSERT OR IGNORE INTO phases (sequence_order, title) VALUES (?, ?)", (p_num, p_name))
        cursor.execute("SELECT phase_id FROM phases WHERE title=?", (p_name,))
        phase_id = cursor.fetchone()[0]

        # Ensure Unit hierarchy exists
        cursor.execute("INSERT OR IGNORE INTO units (phase_id, sequence_order, title) VALUES (?, ?, ?)", (phase_id, u_num, u_name))
        cursor.execute("SELECT unit_id FROM units WHERE title=? AND phase_id=?", (u_name, phase_id))
        unit_id = cursor.fetchone()[0]

        # Ensure Lesson header exists
        l_title = f"Lesson {l_num}"
        cursor.execute("INSERT OR IGNORE INTO lessons (unit_id, sequence_order, title) VALUES (?, ?, ?)", (unit_id, l_num, l_title))
        cursor.execute("SELECT lesson_id FROM lessons WHERE unit_id=? AND sequence_order=?", (unit_id, l_num))
        lesson_id = cursor.fetchone()[0]

        # Fetch the ID of the component type matching Excel ('monologue' or 'dialogue')
        cursor.execute("SELECT component_type_id FROM lesson_component_types WHERE name=?", (c_type.lower(),))
        comp_res = cursor.fetchone()
        if not comp_res:
            print(f"  [ERROR] Content_Type '{c_type}' is invalid in row! Use 'monologue' or 'dialogue'.")
            continue
        comp_type_id = comp_res[0]

        # Cross-reference the correct asset table ID based on type
        if c_type.lower() == 'dialogue':
            # Look up internal dialogue identity code
            cursor.execute("SELECT dialogue_id FROM dialogues WHERE internal_code=?", (target,))
            match = cursor.fetchone()
            assoc_id = match[0] if match else None
        else:
            # Look up word, phrase, or sentence pattern in master content
            cursor.execute("SELECT content_id FROM content WHERE georgian=?", (target,))
            match = cursor.fetchone()
            assoc_id = match[0] if match else None

        # Insert relationship if asset found, warn if missing
        if assoc_id:
            cursor.execute("""
                INSERT OR IGNORE INTO lesson_contents (lesson_id, component_type_id, associated_id)
                VALUES (?, ?, ?)
            """, (lesson_id, comp_type_id, assoc_id))
        else:
            print(f"  [WARNING] Linked target '{target}' not found in database! (Type: {c_type})")


    conn.commit()
    conn.close()
    print("\n✅ Database content_poolbook.db successfully built and populated!")

if __name__ == "__main__":
    main()