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

row = content_df.iloc[0]

print(row["Georgian"])

cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table';"
)

print(cursor.fetchall())

cursor.execute(
    "PRAGMA table_info(content)"
)

for row in cursor.fetchall():
    print(row)

row = content_df.iloc[0]

print(row)

row = content_df.iloc[0]
print(row)

cursor.execute(
    """
    INSERT INTO content
    (
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
        1,  # temporary category id
        row["Georgian"],
        row["Transliteration"],
        row["English"],
        int(row["Difficulty"]),
        int(row["Weight"]),
        str(row["Notes"]) if not pd.isna(row["Notes"]) else "",
        str(row["Image_hint"]) if not pd.isna(row["Image_hint"]) else "",
        1
    )
)

conn.commit()

conn.close()

