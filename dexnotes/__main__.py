import argparse
import sqlite3
import os
import json
from datetime import datetime

DB_FILE = 'notes.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tags TEXT,
            notes TEXT NOT NULL,
            items TEXT,
            deadlines TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_note(args):
    conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, tags, notes, items, deadlines FROM notes
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
        note_id, timestamp, tags, notes, items, deadlines = row
        print(f"🆔 ID: {note_id}")
        print(f"🕒 {timestamp}")
        if tags:
            print(f"🏷️  Tags: {tags}")
        print(f"📝 Notes: {notes}")
        if items:
            try:
                parsed_items = json.loads(items)
                for i in parsed_items:
                    if isinstance(i, dict):
                        print(f"   - [{i.get('status', '?')}] {i.get('text', '')}")
                    else:
                        print(f"   - {i}")
            except Exception:
                print("⚠️  Failed to parse items.")
        if deadlines:
            try:
                print(f"📅 Deadlines: {json.loads(deadlines)}")
            except Exception:
                print("⚠️  Failed to parse deadlines.")
        print("-" * 40)

def list_customers(args):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT customer FROM notes ORDER BY customer')
    customers = cursor.fetchall()
    conn.close()

    print("\n👥 Customers:\n")
    for (cust,) in customers:
        print(f"- {cust}")
    print()

def edit_note(args):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE id = ?', (args.id,))
    note = cursor.fetchone()

    if not note:
        print(f"❌ Note with ID {args.id} not found.")
        return

    updated_fields = {
        "customer": args.customer or note[1],
        "timestamp": datetime.fromisoformat(args.date).isoformat() if args.date else datetime.utcnow().isoformat(),
        "tags": ','.join(args.tags) if args.tags else note[3],
        "notes": args.notes or note[4],
        "items": json.dumps(
            [{"text": item, "status": "open"} for item in args.items]
        ) if args.items else note[5],
        "deadlines": json.dumps(args.deadlines) if args.deadlines else note[6],
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
    conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
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

def list_notes(args):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, customer, timestamp, notes, items FROM notes
        ORDER BY timestamp DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No notes found.")
        return

    print("\n🗂️ All Notes:\n")
    for note_id, customer, timestamp, notes, items in rows:
        summary = notes.split('\n')[0][:60] + ('...' if len(notes) > 60 else '')
        print(f"🆔 {note_id} | 🧑 {customer} | 🕒 {timestamp}")
        print(f"   📝 {summary}")

        if items:
            try:
                parsed_items = json.loads(items)
                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        if isinstance(item, dict):
                            status = item.get("status", "open")
                            icon = "✅" if status == "closed" else "🔄"
                            print(f"   - {icon} {item.get('text', '')}")
            except Exception:
                print("   ⚠️ Failed to parse items")

        print("-" * 60)



def main():
    init_db()
    parser = argparse.ArgumentParser(description='Customer Notes CLI')
    subparsers = parser.add_subparsers(dest='command')

    # Add
    parser_add = subparsers.add_parser('add', help='Add a new note')
    parser_add.add_argument('--customer', required=True)
    parser_add.add_argument('--notes', required=True)
    parser_add.add_argument('--tags', nargs='*')
    parser_add.add_argument('--items', nargs='*')
    parser_add.add_argument('--deadlines', nargs='*')
    parser_add.add_argument('--date', help='Optional custom date in YYYY-MM-DD format')
    parser_add.set_defaults(func=add_note)

    # View
    parser_view = subparsers.add_parser('view', help='View notes by customer')
    parser_view.add_argument('--customer', required=True)
    parser_view.set_defaults(func=view_notes)

    # Customers
    parser_customers = subparsers.add_parser('customers', help='List all customers')
    parser_customers.set_defaults(func=list_customers)

    # Edit
    parser_edit = subparsers.add_parser('edit', help='Edit a note by ID')
    parser_edit.add_argument('--id', type=int, required=True)
    parser_edit.add_argument('--customer')
    parser_edit.add_argument('--notes')
    parser_edit.add_argument('--tags', nargs='*')
    parser_edit.add_argument('--items', nargs='*')
    parser_edit.add_argument('--deadlines', nargs='*')
    parser_edit.add_argument('--date', help='Optional new date in YYYY-MM-DD format')
    parser_edit.set_defaults(func=edit_note)

    # Delete
    parser_delete = subparsers.add_parser('delete', help='Delete a note by ID')
    parser_delete.add_argument('--id', type=int, required=True)
    parser_delete.set_defaults(func=delete_note)

    # Standup
    parser_standup = subparsers.add_parser('standup', help='Run interactive standup session')
    parser_standup.set_defaults(func=standup_run)

    # Migrate
    parser_migrate = subparsers.add_parser('migrate', help='Migrate plain items to structured format')
    parser_migrate.set_defaults(func=migrate_items_to_structured)

    # List all notes
    parser_list = subparsers.add_parser('list', help='List all notes')
    parser_list.set_defaults(func=list_notes)


    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
