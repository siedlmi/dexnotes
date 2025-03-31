import typer
from dexnotes.db import (init_db, migrate_items_to_structured)
from dexnotes.notes import (
    add_note, edit_note, delete_note, view_notes,
    list_notes, list_customers, list_items, archive_note,
    standup_run, search_notes
)
from dexnotes.export import export_notes

app = typer.Typer(
    help="Dexnotes CLI - manage customer notes, standups, and exports.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]}
)
note_app = typer.Typer()

@app.command()
def migrate():
    migrate_items_to_structured()

@app.command()
def export(format: str, out: str = None):
    export_notes(format=format, out=out)

@note_app.command()
def add(customer: str, notes: str, tags: list[str] = None, items: list[str] = None, deadlines: list[str] = None, date: str = None):
    add_note(customer=customer, notes=notes, tags=tags, items=items, deadlines=deadlines, date=date)

@note_app.command()
def view(customer: str):
    view_notes(customer=customer)

@note_app.command()
def search(query: str):
    search_notes(query=query)

@note_app.command()
def customers():
    list_customers()

@note_app.command()
def edit(id: int, customer: str = None, notes: str = None, tags: list[str] = None, items: list[str] = None, deadlines: list[str] = None, date: str = None):
    edit_note(id=id, customer=customer, notes=notes, tags=tags, items=items, deadlines=deadlines, date=date)

@note_app.command()
def delete(id: int):
    delete_note(id=id)

@note_app.command()
def archive(id: int):
    archive_note(id=id)

@note_app.command()
def list(tag: str = None, all: bool = False):
    list_notes(tag=tag, all=all)

@note_app.command()
def items(status: str = 'all'):
    list_items(status=status)

app.add_typer(note_app, name="note")

@app.command()
def standup():
    standup_run()

if __name__ == '__main__':
    app()
