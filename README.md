# Bedrock

A tool for first-principles thinking. You write down a claim, break it into the
things it rests on, and keep going until you hit something you can't argue with.
Nodes are typed — **claim**, **assumption**, **axiom**, **evidence** — and new
nodes default to *assumption*, so calling something bedrock is a deliberate act
rather than the path of least resistance.

The **Rebuild** toggle dims every node that isn't on a path down to an axiom.
What stays lit is the part of your argument that's actually grounded.

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000. The database file is created on first start.

Interactive API docs are at http://127.0.0.1:8000/docs.

## Tests

```bash
python -m pytest -v
```

Nine tests covering the happy path and the failure cases: unknown ids return
404, an invalid `kind` returns 422, and deleting a parent removes its subtree.
Each test runs against a fresh temporary database via an autouse fixture, so
they're order-independent and never touch `bedrock.db`.

## How it's put together

```
app/db.py       connections and schema      — knows SQLite
app/models.py   request/response shapes     — knows validation
app/store.py    node operations             — knows the data
app/main.py     routes                      — knows HTTP
static/         the interface               — knows the DOM
```

Imports only ever point downward. `store.py` has no idea what an HTTP status
code is: it returns `None` when a node doesn't exist, and `main.py` is the only
layer that decides `None` means 404. That's what makes the data layer testable
without a server, and what would let the whole API be swapped for a CLI without
touching the logic underneath.

**Some specific decisions:**

- **Tree building happens on the server** (`GET /api/tree`). The flat table has
  `parent_id` pointers; the frontend wants nesting. Doing the conversion in one
  place, in one language, beats reimplementing it in JavaScript.
- **`ON DELETE CASCADE` with `PRAGMA foreign_keys = ON`.** Foreign keys are off
  by default in SQLite, so the pragma is set on every connection. Deleting a
  node removes its descendants in the database rather than in application code.
- **Partial updates are guarded twice.** `exclude_unset=True` strips fields the
  client never sent, and `store.update_node` drops anything `None`. Sending
  `{"kind": "axiom"}` can't blank out the text.
- **Dynamic SQL is whitelisted.** Column names can't be parameterised, so
  `update_node` interpolates them — but only after checking each against a
  fixed set. Values always go through `?` placeholders.
- **The frontend refetches after every change** instead of patching the DOM in
  place. Slower in principle, but the server stays the single source of truth
  and the two can't drift.

## Known limits

- One shared tree; no accounts, no multi-user support.
- No undo. Deletes are confirmed with a second click, not reversible.
- Reordering siblings isn't supported — children sort by creation time.
- SQLite with default settings; fine for one person, not for concurrent writers.
