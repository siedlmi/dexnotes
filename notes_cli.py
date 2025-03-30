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
    timestamp = datetime.utcnow().isoformat()
    tags = ','.join(args.tags) if args.tags else None
    items = json.dumps(args.items) if args.items else None
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
            print(f"📌 Items: {json.loads(items)}")
        if deadlines:
            print(f"📅 Deadlines: {json.loads(deadlines)}")
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
        "timestamp": datetime.utcnow().isoformat(),  # updated on edit
        "tags": ','.join(args.tags) if args.tags else note[3],
        "notes": args.notes or note[4],
        "items": json.dumps(args.items) if args.items else note[5],
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
    parser_edit.set_defaults(func=edit_note)

    # Delete
    parser_delete = subparsers.add_parser('delete', help='Delete a note by ID')
    parser_delete.add_argument('--id', type=int, required=True)
    parser_delete.set_defaults(func=delete_note)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
