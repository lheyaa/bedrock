"""Data operations for nodes. Knows nothing about HTTP."""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.db import connect 

@contextmanager
def _tx(): 
    """Open a connection, commit on success, always close."""
    conn = connect()
    try: 
        yield conn
        conn.commit()
    finally: 
        conn.close()
    
def create_node(text: str, kind: str, note: str, parent_id: Optional[str]) -> dict[str, Any]:
    node_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    with _tx() as conn:
        conn.execute(
            "INSERT INTO nodes (id, text, kind, note, parent_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)", 
            (node_id, text, kind, note, parent_id, created_at),
        )
    return get_node(node_id)

def list_nodes() -> list[dict[str, Any]]:
    """Every node, oldest first."""
    with _tx() as conn: 
        rows = conn.execute(
            "SELECT id, text, kind, note, parent_id, created_at"
            " FROM nodes ORDER BY created_at"
        ).fetchall()
    return [dict(row) for row in rows]

def get_node(node_id: str) -> Optional[dict[str, Any]]:
    """One node by id, or None if it does not exist."""
    with _tx() as conn: 
        row = conn.execute(
            "SELECT id, text, kind, note, parent_id, created_at"
            " FROM nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
    return dict(row) if row is not None else None

def delete_node(node_id: str) -> bool: 
    """"Delete a node and its whole subtree. True if it existed."""
    with _tx() as conn:
        cursor = conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        deleted = cursor.rowcount
    return deleted > 0

def update_node(node_id: str, changes: dict[str, Any]) -> Optional[dict]:
    allowed = {"text", "kind", "note"}
    updates = {k: v for k, v in changes.items()
               if k in allowed and v is not None}
    if not updates:
        return get_node(node_id)
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = [*updates.values(), node_id]
    with _tx() as conn:
        conn.execute(f"UPDATE nodes SET {assignments} WHERE id = ?", values)
    return get_node(node_id)

def build_tree(nodes: list[dict]) -> list[dict]:
    """Turn a flat list with parent pointers into nested structure."""
    indexed = {n["id"]: {**n, "children": []} for n in nodes}
    roots = []
    for node in indexed.values():
        parent = indexed.get(node["parent_id"])
        if parent is None:
            roots.append(node)
        else:
            parent["children"].append(node)
    return roots

