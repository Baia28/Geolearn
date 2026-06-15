import sqlite3
import json

conn = sqlite3.connect("database/content_pool.db")
cursor = conn.cursor()

with open("data/curriculum.json", "r", encoding="utf-8") as f:
    lesson = json.load(f)

print(f"\nLesson: {lesson['title']}\n")

for activity in lesson["activities"]:

    if activity["type"] == "learn":

        cursor.execute(
            "SELECT georgian, english FROM content WHERE content_id=?",
            (activity["content_ref"],)
        )

        row = cursor.fetchone()

        print(
            f"{activity['content_ref']} -> "
            f"{row[0]} = {row[1]}"
        )

conn.close()