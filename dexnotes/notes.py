from dexnotes.models import Note
from dexnotes.db import get_connection
import json
from datetime import datetime

def add_note(args):
    conn = get_connection()
    cursor = conn.cursor()
    if args.date:
        try:
            timestamp = datetime.fromisoformat(args.date).isoformat()
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD.")
            return
    else:
        timestamp = datetime.utcnow().isoformat()    
    tags = ','.join(args.tags) if args.tags else None

    if args.items:
        structured_items = [{"text": item, "status": "open"} for item in args.items]
        items = json.dumps(structured_items)
    else:
        items = None

    deadlines = json.dumps(args.deadlines) if args.deadlines else None

    cursor.execute('''
        INSERT INTO notes (customer, timestamp, tags, notes, items, deadlines)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (args.customer, timestamp, tags, args.notes, items, deadlines))

    conn.commit()
    conn.close()
    print(f"✅ Note added for {args.customer}.")

def view_notes(args):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, customer, timestamp, tags, notes, items, deadlines, archived FROM notes
        WHERE customer = ?
        ORDER BY timestamp DESC
    ''', (args.customer,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"No notes found for {args.customer}.")
        return

    print(f"\n📒 Notes for {args.customer}:\n")
    for row in rows:
        note = Note(*row)
        print(f"🆔 ID: {note.id}")
        print(f"🕒 {note.timestamp}")
        if note.tags:
            print(f"🏷️  Tags: {note.tags}")
        print(f"📝 Notes: {note.notes}")
        if note.items:
            try:
                parsed_items = json.loads(note.items)
                for i in parsed_items:
                    if isinstance(i, dict):
                        print(f"   - [{i.get('status', '?')}] {i.get('text', '')}")
                    else:
                        print(f"   - {i}")
            except Exception:
                print("⚠️  Failed to parse items.")
        if note.deadlines:
            try:
                print(f"📅 Deadlines: {json.loads(note.deadlines)}")
            except Exception:
                print("⚠️  Failed to parse deadlines.")
        print("-" * 40)

def search_notes(args):
    conn = get_connection()
    cursor = conn.cursor()
    query = '''
        SELECT id, customer, timestamp, tags, notes, items, deadlines, archived FROM notes
        WHERE notes LIKE ? OR tags LIKE ?
    '''
    params = [f'%{args.query}%', f'%{args.query}%']
    cursor.execute(query, params)
    rows = cursor.fetchall()

    matching_notes = []
    for row in rows:
        note = Note(*row)
        matching_notes.append(note)

        if note.items:
            try:
                parsed_items = json.loads(note.items)
                for item in parsed_items:
                    if isinstance(item, dict) and args.query in item.get('text', ''):
                        matching_notes.append(note)
                        break
            except Exception:
                print("⚠️  Failed to parse items")

    conn.close()

    if not matching_notes:
        print("📭 No matching notes found.")
        return

    print("\n🗂️ Matching Notes:\n")
    for note in matching_notes:
        summary = note.notes.split('\n')[0][:60] + ('...' if len(note.notes) > 60 else '')
        print(f"🆔 {note.id} | 🧑 {note.customer} | 🕒 {note.timestamp}")
        print(f"   📝 {summary}")

        if note.tags:
            print(f"   🏷️ Tags: {note.tags}")

        if note.items:
            try:
                parsed_items = json.loads(note.items)
                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        if isinstance(item, dict):
                            status = item.get("status", "open")
                            icon = "✅" if status == "closed" else "🔄"
                            print(f"   - {icon} {item.get('text', '')}")
            except Exception:
                print("   ⚠️ Failed to parse items")

        print("-" * 60)

def list_customers(args):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT customer FROM notes ORDER BY customer')
    customers = cursor.fetchall()
    conn.close()

    print("\n👥 Customers:\n")
    for (cust,) in customers:
        print(f"- {cust}")
    print()

def edit_note(args):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE id = ?', (args.id,))
    note_data = cursor.fetchone()

    if not note_data:
        print(f"❌ Note with ID {args.id} not found.")
        return

    note = Note(*note_data)

    updated_fields = {
        "customer": args.customer or note.customer,
        "timestamp": datetime.fromisoformat(args.date).isoformat() if args.date else datetime.utcnow().isoformat(),
        "tags": ','.join(args.tags) if args.tags else note.tags,
        "notes": args.notes or note.notes,
        "items": json.dumps(
            [{"text": item, "status": "open"} for item in args.items]
        ) if args.items else note.items,
        "deadlines": json.dumps(args.deadlines) if args.deadlines else note.deadlines,
    }

    cursor.execute('''
        UPDATE notes
        SET customer = ?, timestamp = ?, tags = ?, notes = ?, items = ?, deadlines = ?
        WHERE id = ?
    ''', (
        updated_fields["customer"],
        updated_fields["timestamp"],
        updated_fields["tags"],
        updated_fields["notes"],
        updated_fields["items"],
        updated_fields["deadlines"],
        args.id
    ))

    conn.commit()
    conn.close()
    print(f"✏️ Note {args.id} updated.")

def delete_note(args):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE id = ?', (args.id,))
    note = cursor.fetchone()

    if not note:
        print(f"❌ Note with ID {args.id} not found.")
        return

    confirm = input(f"⚠️ Are you sure you want to delete note ID {args.id}? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    cursor.execute('DELETE FROM notes WHERE id = ?', (args.id,))
    conn.commit()
    conn.close()
    print(f"🗑️ Note {args.id} deleted.")

def standup_run(args):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer, items FROM notes')
    notes = cursor.fetchall()

    report = {}
    updated_notes = []

    print("\n🟢 Starting standup session...\n")

    for note_id, customer, items_json in notes:
        if not items_json:
            continue

        try:
            items = json.loads(items_json)
            # Auto-convert legacy format
            if isinstance(items, list) and all(isinstance(i, str) for i in items):
                items = [{"text": i, "status": "open"} for i in items]
        except Exception:
            print(f"⚠️ Skipping note {note_id} (invalid item format)")
            continue

        if not isinstance(items, list) or not any(i.get("status") == "open" for i in items if isinstance(i, dict)):
            continue

        print(f"\n📋 Customer: {customer} (Note ID: {note_id})")

        for idx, item in enumerate(items):
            if not isinstance(item, dict) or item.get("status") != "open":
                continue

        print(f"\n🔹 Item: {item['text']}")
        choice = input("   [s]kip, [u]pdate, [c]lose, [a]dd item? ").strip().lower()

        if choice == 'c':
            item['status'] = 'closed'
            report.setdefault(customer, []).append(f"✅ Closed: {item['text']}")
        elif choice == 'u':
            new_text = input("   ✏️  New text: ").strip()
            old_text = item['text']
            item['text'] = new_text
            report.setdefault(customer, []).append(f"🔄 Updated: {old_text} → {new_text}")
        elif choice == 'a':
            new_item_text = input("   ➕ New item text: ").strip()
            new_item = {"text": new_item_text, "status": "open"}
            items.append(new_item)
            report.setdefault(customer, []).append(f"➕ Added item: {new_item_text}")
        elif choice == 's':
            report.setdefault(customer, []).append(f"⏭️ Skipped: {item['text']}")
        else:
            print("   ❓ Invalid choice, skipping.")
            report.setdefault(customer, []).append(f"⏭️ Skipped (invalid input): {item['text']}")

        updated_notes.append((json.dumps(items), note_id))

    # Update notes in DB
    for items_json, note_id in updated_notes:
        cursor.execute('UPDATE notes SET items = ? WHERE id = ?', (items_json, note_id))

    conn.commit()
    conn.close()

    # Generate markdown report
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_lines = [f"# Dexnotes Standup Report - {date_str}", ""]
    for customer, actions in report.items():
        md_lines.append(f"## {customer}")
        for action in actions:
            md_lines.append(f"- {action}")
        md_lines.append("")

    report_md = "\n".join(md_lines)
    report_filename = f"standup_report_{date_str}.md"
    with open(report_filename, 'w', encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n📄 Standup complete. Markdown report saved as: {report_filename}")

def list_notes(args):
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT id, customer, timestamp, tags, notes, items, deadlines, archived FROM notes
    '''
    conditions = []
    params = []

    if not args.all:
        conditions.append("archived = 0")

    if args.tag:
        conditions.append("tags LIKE ?")
        params.append(f'%{args.tag}%')

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' ORDER BY timestamp DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No notes found.")
        return

    print("\n🗂️ All Notes:\n")
    for row in rows:
        note = Note(*row)
        summary = note.notes.split('\n')[0][:60] + ('...' if len(note.notes) > 60 else '')
        print(f"🆔 {note.id} | 🧑 {note.customer} | 🕒 {note.timestamp}")
        print(f"   📝 {summary}")

        if note.tags:
            print(f"   🏷️ Tags: {note.tags}")

        if note.items:
            try:
                parsed_items = json.loads(note.items)
                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        if isinstance(item, dict):
                            status = item.get("status", "open")
                            icon = "✅" if status == "closed" else "🔄"
                            print(f"   - {icon} {item.get('text', '')}")
            except Exception:
                print("   ⚠️ Failed to parse items")

        print("-" * 60)

def list_items(args):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer, items FROM notes')
    notes = cursor.fetchall()
    conn.close()

    filtered_items = []

    for note_id, customer, items_json in notes:
        if not items_json:
            continue

        try:
            items = json.loads(items_json)
        except Exception:
            print(f"⚠️ Failed to parse items for note {note_id}.")
            continue

        for item in items:
            if isinstance(item, dict):
                if args.status == 'all' or item.get('status') == args.status:
                    filtered_items.append((note_id, customer, item['text'], item['status']))

    if not filtered_items:
        print("📭 No items found.")
        return

    print("\n🗂️ All Items:\n")
    for note_id, customer, text, status in filtered_items:
        print(f"🆔 Note ID: {note_id} | 🧑 Customer: {customer} | 📋 Item: {text} | Status: {status}")

def archive_note(args):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM notes WHERE id = ?', (args.id,))
    note = cursor.fetchone()

    if not note:
        print(f"❌ Note with ID {args.id} not found.")
        return

    cursor.execute('UPDATE notes SET archived = 1 WHERE id = ?', (args.id,))
    conn.commit()
    conn.close()
    print(f"📦 Note {args.id} archived.")