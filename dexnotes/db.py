# db.py
import sqlite3
import os
import json


DB_FILE = os.path.expanduser('~/.dexnotes.db')

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tags TEXT,
            notes TEXT NOT NULL,
            items TEXT,
            deadlines TEXT,
            archived BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def migrate_items_to_structured(args=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, items FROM notes')
    rows = cursor.fetchall()

    for note_id, items_json in rows:
        if not items_json:
            continue
        try:
            raw_items = json.loads(items_json)
            if isinstance(raw_items, list) and all(isinstance(i, str) for i in raw_items):
                structured = [{"text": i, "status": "open"} for i in raw_items]
                cursor.execute('UPDATE notes SET items = ? WHERE id = ?', (json.dumps(structured), note_id))
        except Exception:
            print(f"❌ Could not migrate note {note_id}")
            continue

    conn.commit()
    conn.close()
    print("✅ Migration complete.")