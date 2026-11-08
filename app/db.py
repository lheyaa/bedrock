"""Database connection and schema for Bedrock."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bedrock.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY, 
    text TEXT NOT NULL, 
    kind TEXT NOT NULL DEFAULT 'assumption',
    note TEXT NOT NULL DEFAULT '',
    parent_id TEXT REFERENCES nodes(id) ON DELETE CASCADE, 
    created_at TEXT NOT NULL
);
"""

def connect() -> sqlite3.Connection:
    """Open a connection with sensible defaults"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None: 
    """Create the nodes table if it does not already exist."""
    conn = connect()
    try: 
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    
if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")

