import sqlite3
import pandas as pd

file = "data/content_master.xlsx"

content_df = pd.read_excel(
    file,
    sheet_name="Content_Master"
)

conn = sqlite3.connect(
    "database/content.db"
)

cursor = conn.cursor()


cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table';"
)

##print(cursor.fetchall())

DEBUG = False

if DEBUG:
    cursor.execute("PRAGMA table_info(content)")
    for r in cursor.fetchall():
        print(r)




def safe_int(value, default=1):
    if pd.isna(value):
        return default
    return int(value)

CATEGORY_MAP = {
    "vocab": 1,
    "vocabulary": 1,
    "pattern": 2,
}

for _, row in content_df.iterrows():
    
    category_type = str(row["Type"]).strip().lower()
    category_id = CATEGORY_MAP.get(category_type)

    if category_id is None:
        print(f"Skipping unknown category: {category_type}")
        continue
        
    cursor.execute(
        """
        INSERT OR IGNORE INTO content (
            category_id,
            georgian,
            transliteration,
            english,
            difficulty,
            mastery_weight,
            notes,
            image_hint,
            active,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            category_id,
            row["Georgian"],
            row["Transliteration"],
            row["English"],
            safe_int(row["Difficulty"], 1),
            safe_int(row["Weight"],1),
            str(row["Notes"]) if not pd.isna(row["Notes"]) else "",
            str(row["Image_hint"]) if not pd.isna(row["Image_hint"]) else "",
            1
        )
    )

conn.commit()

conn.close()