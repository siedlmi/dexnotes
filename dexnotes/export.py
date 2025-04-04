from dexnotes.db import get_connection
from datetime import datetime
import json
from dexnotes.models import Note
from typing import Optional

def export_notes(format: str, out: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer, timestamp, tags, notes, items, deadlines, archived FROM notes')
    rows = cursor.fetchall()
    conn.close()
    
    # Prepare export data
    notes_list = []
    for row in rows:
        note = Note(
            id=row[0],
            customer=row[1],
            timestamp=row[2],
            tags=row[3],
            notes=row[4],
            items=json.loads(row[5]) if row[5] else None,
            deadlines=json.loads(row[6]) if row[6] else None,
            archived=bool(row[7])
        )
        notes_list.append(note)

    date_str = datetime.now().strftime("%Y-%m-%d")
    export_format = format.lower()
    if export_format == 'json':
        output = json.dumps(notes_list, indent=2)
        default_filename = f"notes_{date_str}.json"
    elif export_format == 'markdown':
        lines = [f"# Notes Export - {date_str}", ""]
        for note in notes_list:
            lines.append(f"## Note ID: {note.id} - {note.customer}")
            lines.append(f"**Timestamp:** {note.timestamp}")
            if note.tags:
                lines.append(f"**Tags:** {note.tags}")
            lines.append("")
            lines.append(note.notes)
            lines.append("\n---\n")
        output = "\n".join(lines)
        default_filename = f"notes_{date_str}.md"
    else:
        print("❌ Unsupported format.")
        return

    filename = out if out else default_filename
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"✅ Notes exported to {filename}.")