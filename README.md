
# 📝 dexnotes

**dexnotes** is a command-line tool to help delivery managers and technical leads take structured notes, track action items, and run standups across multiple customers — all from your terminal.

## 🚀 Features

- Add and view notes per customer
- Track action items and deadlines
- Interactive standup mode to review and update progress
- Markdown report generation for standups
- SQLite-based local storage (no external dependencies)
- Easy CLI usage

---

## 📦 Installation

Clone the repo and install using `pip`:

```bash
git clone https://github.com/your-username/dexnotes.git
cd dexnotes
pip install -e .
```

> Requires Python 3.8+

---

## ⚡ Usage

### Add a new note:

```bash
dexnotes add --customer "Acme Corp" --notes "Kickoff complete" \
             --items "Send contract" "Create shared Slack channel" \
             --tags onboarding high-priority
```

### View notes for a customer:

```bash
dexnotes view --customer "Acme Corp"
```

### Run a standup session:

```bash
dexnotes standup
```

You'll be prompted to skip, update, or close each open item. A Markdown report is generated at the end.

### List all customers:

```bash
dexnotes customers
```

### Edit a note:

```bash
dexnotes edit --id 3 --items "Reschedule meeting"
```

### Delete a note:

```bash
dexnotes delete --id 3
```

---

## 🛠 Migrate old notes (if upgrading)

To convert plain string-based items to structured format:

```bash
dexnotes migrate
```

---

## 📁 Data Storage

- Notes are stored in a local `notes.db` SQLite file.
- Items are stored as structured JSON (with `text` and `status`).

---

## 📄 Example Standup Report

After running `dexnotes standup`, you'll get a report like:

```markdown
# Dexnotes Standup Report - 2025-03-31

## Acme Corp
- ✅ Closed: Create shared Slack channel
- 🔄 Updated: Send contract → Send final legal-reviewed contract
- ⏭️ Skipped: Set up monitoring tools
```

---

## 📚 License

MIT © [Your Name](https://github.com/your-username)
```

---