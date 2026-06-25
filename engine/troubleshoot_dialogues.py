import sqlite3

DATABASE_NAME = "database/content_poolbook.db"

def inspect_dialogue_system():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔍 DIALOGUE SYSTEM DIAGNOSTIC RUN 🔍")
    print("=" * 60)

    # 1. CHECK TABLES SCHEMA
    print("\n--- 1. Verifying Database Schema Structure ---")
    tables_to_check = ['dialogues', 'dialogue_lines', 'content']
    for table in tables_to_check:
        try:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            if columns:
                col_info = [f"{col[1]} ({col[2]})" for col in columns]
                print(f"✅ Table '{table}' exists. Columns: {', '.join(col_info)}")
            else:
                print(f"❌ Table '{table}' has no columns or does not exist!")
        except Exception as e:
            print(f"❌ Error checking table '{table}': {e}")

    # 2. COUNT REGISTERED DIALOGUES
    print("\n--- 2. Inspecting Master Dialogue Entries ---")
    try:
        cursor.execute("SELECT dialogue_id, internal_code FROM dialogues LIMIT 5;")
        dialogue_rows = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM dialogues;")
        total_d = cursor.fetchone()[0]
        print(f"📊 Total dialogues registered in DB: {total_d}")
        print("📋 Sample Entries (First 5):")
        for row in dialogue_rows:
            print(f"  - ID: {row[0]} | Code/Title: '{row[1]}'")
    except Exception as e:
        print(f"❌ Error fetching from 'dialogues' table: {e}")

    # 3. CHECK FOR ORPHAN LINES
    print("\n--- 3. Verifying Conversation Line Counts ---")
    try:
        cursor.execute("SELECT COUNT(*) FROM dialogue_lines;")
        total_lines = cursor.fetchone()[0]
        print(f"📊 Total script lines across all conversations: {total_lines}")
        
        # Look for dialogue lines not attached to a valid dialogue ID
        cursor.execute("""
            SELECT COUNT(*) FROM dialogue_lines 
            WHERE dialogue_id NOT IN (SELECT dialogue_id FROM dialogues)
        """)
        orphans = cursor.fetchone()[0]
        if orphans > 0:
            print(f"⚠️ WARNING: {orphans} rows in dialogue_lines point to a dialogue_id that doesn't exist!")
        else:
            print("✅ All script lines correctly point to parent conversations.")
    except Exception as e:
        print(f"❌ Error counting script lines: {e}")

    # 4. TEST DICTIONARY LINKING (THE LEFT JOIN)
    print("\n--- 4. Testing Master Vocabulary Mapping Integrity ---")
    try:
        cursor.execute("""
            SELECT dl.dialogue_id, dl.speaker, dl.georgian_content, c.english
            FROM dialogue_lines dl
            LEFT JOIN content c ON dl.georgian_content = c.georgian
            LIMIT 10;
        """)
        join_sample = cursor.fetchall()
        print("📋 Sample Lookups (Script Line -> Dictionary Translation):")
        for row in join_sample:
            d_id, speaker, geo, eng = row
            status = f"✅ Links to '{eng}'" if eng else "⚠️ MISSING FROM DICTIONARY (Returns None)"
            # Truncate strings for clear terminal printing
            geo_trunc = geo[:15] + "..." if len(geo) > 15 else geo
            print(f"  [Dialogue ID {d_id}] Speaker {speaker}: '{geo_trunc}' -> {status}")
            
        # Count exact mismatches
        cursor.execute("""
            SELECT COUNT(*) 
            FROM dialogue_lines dl
            LEFT JOIN content c ON dl.georgian_content = c.georgian
            WHERE c.english IS NULL;
        """)
        missing_matches = cursor.fetchone()[0]
        print(f"\n📊 Total Dialogue Lines failing to match dictionary: {missing_matches}")
        if missing_matches > 0:
            print("💡 Tip: This happens due to trailing spaces or minor punctuation differences between sheets (e.g., 'გამარჯობა!' vs 'გამარჯობა').")
            
    except Exception as e:
        print(f"❌ Error executing dictionary relational lookup test: {e}")

    print("\n" + "=" * 60)
    conn.close()

if __name__ == "__main__":
    inspect_dialogue_system()