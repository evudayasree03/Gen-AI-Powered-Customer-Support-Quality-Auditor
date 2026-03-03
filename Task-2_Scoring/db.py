import sqlite3
import json

conn = sqlite3.connect("call_history.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    transcript TEXT,
    summary TEXT,
    scores TEXT,
    duration TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


def save_call(filename, transcript, summary, scores, duration):

    cursor.execute(
        """
        INSERT INTO calls (filename, transcript, summary, scores, duration)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            filename,
            transcript,
            summary,
            json.dumps(scores),
            duration
        )
    )

    conn.commit()


def get_calls():

    cursor.execute("SELECT * FROM calls ORDER BY created_at DESC")

    return cursor.fetchall()