import argparse
from dexnotes.db import (init_db, migrate_items_to_structured)
from dexnotes.notes import (
    add_note, edit_note, delete_note, view_notes,
    list_notes, list_customers, list_items, archive_note,
    standup_run, search_notes
)
from dexnotes.export import export_notes

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

    # Search
    parser_search = subparsers.add_parser('search', help='Search notes by keyword')
    parser_search.add_argument('--query', required=True, help='Search keyword')
    parser_search.set_defaults(func=search_notes)

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

    # Archive
    parser_archive = subparsers.add_parser('archive', help='Archive a note by ID')
    parser_archive.add_argument('--id', type=int, required=True)
    parser_archive.set_defaults(func=archive_note)

    # Standup
    parser_standup = subparsers.add_parser('standup', help='Run interactive standup session')
    parser_standup.set_defaults(func=standup_run)

    # Migrate
    parser_migrate = subparsers.add_parser('migrate', help='Migrate plain items to structured format')
    parser_migrate.set_defaults(func=migrate_items_to_structured)

    # List all notes
    parser_list = subparsers.add_parser('list', help='List all notes')
    parser_list.add_argument('--tag', help='Filter notes containing a specific tag')
    parser_list.add_argument('--all', action='store_true', help='Include archived notes')
    parser_list.set_defaults(func=list_notes)

    # List all items
    parser_items = subparsers.add_parser('items', help='List all items across notes')
    parser_items.add_argument('--status', choices=['open', 'closed', 'all'], default='all', help='Filter by item status')
    parser_items.set_defaults(func=list_items)

    # Export command
    parser_export = subparsers.add_parser('export', help='Export all notes')
    parser_export.add_argument('--format', required=True, choices=['json', 'markdown'], help='Export format')
    parser_export.add_argument('--out', help='Output filename')
    parser_export.set_defaults(func=export_notes)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
