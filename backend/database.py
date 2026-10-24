"""
SQLite Database Engine with FTS5 Full-Text Search
- Manages connection lifecycle
- Auto-initializes schema, indexes, and FTS5 virtual table
- Safe bulk import & indexing
- Atomic memory and settings mutations
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "chat.db")
WRAPPED_PHOTOS_DIR = os.path.join(DB_DIR, "wrapped_photos")


def get_db_connection() -> sqlite3.Connection:
    """Create a database connection with Row factory and foreign keys enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(WRAPPED_PHOTOS_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Initialize database tables, indexes, and full-text search engine."""
    conn = get_db_connection()
    with conn:
        # Settings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Messages table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_str TEXT,
                time_str TEXT,
                iso_date TEXT,
                iso_datetime TEXT,
                timestamp INTEGER,
                sender_raw TEXT,
                sender_clean TEXT,
                is_vinu INTEGER DEFAULT 0,
                is_bhumi INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0,
                content TEXT,
                message_type TEXT DEFAULT 'text',
                is_edited INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                emoji_count INTEGER DEFAULT 0,
                emojis_json TEXT DEFAULT '[]',
                word_count INTEGER DEFAULT 0,
                char_count INTEGER DEFAULT 0
            )
        """)

        # Indexes for fast querying & timeline aggregation
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_iso_date ON messages(iso_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_clean)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_vinu ON messages(is_vinu)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_bhumi ON messages(is_bhumi)")

        # Full-Text Search virtual table (FTS5)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                content,
                sender_clean UNINDEXED,
                iso_date UNINDEXED,
                content='messages',
                content_rowid='id'
            )
        """)

        # Triggers to keep FTS5 synchronized with messages table
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content, sender_clean, iso_date)
                VALUES (new.id, new.content, new.sender_clean, new.iso_date);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                INSERT INTO messages_fts(messages_fts, rowid, content, sender_clean, iso_date)
                VALUES('delete', old.id, old.content, old.sender_clean, old.iso_date);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
                INSERT INTO messages_fts(messages_fts, rowid, content, sender_clean, iso_date)
                VALUES('delete', old.id, old.content, old.sender_clean, old.iso_date);
                INSERT INTO messages_fts(rowid, content, sender_clean, iso_date)
                VALUES (new.id, new.content, new.sender_clean, new.iso_date);
            END;
        """)

        # Memories table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                tags TEXT,
                created_at INTEGER,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_msg ON memories(message_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_cat ON memories(category)")

        # Funny Moments Flags
        conn.execute("""
            CREATE TABLE IF NOT EXISTS funny_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL UNIQUE,
                status TEXT DEFAULT 'suggested',
                signals TEXT,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_funny_status ON funny_flags(status)")

        # Ensure no duplicate memories exist per message
        conn.execute("""
            DELETE FROM memories 
            WHERE id NOT IN (
                SELECT MAX(id) FROM memories GROUP BY message_id
            )
        """)

        # Wrapped Personal Photos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS wrapped_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                caption TEXT DEFAULT '',
                slide_id TEXT DEFAULT 'moments',
                created_at INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_wrapped_photos_slide ON wrapped_photos(slide_id)")

    conn.close()


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve a setting value."""
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    """Set or update a setting value."""
    conn = get_db_connection()
    with conn:
        conn.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
    conn.close()


def delete_setting(key: str):
    """Delete a setting key."""
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM settings WHERE key = ?", (key,))
    conn.close()


def bulk_insert_messages(messages: List[Dict[str, Any]]) -> int:
    """Insert a parsed list of messages into the database and sync FTS5."""
    if not messages:
        return 0

    conn = get_db_connection()
    with conn:
        # Prepare records for batch insertion
        records = [
            (
                m["date_str"],
                m["time_str"],
                m["iso_date"],
                m["iso_datetime"],
                m["timestamp"],
                m["sender_raw"],
                m["sender_clean"],
                1 if m["is_vinu"] else 0,
                1 if m["is_bhumi"] else 0,
                1 if m["is_system"] else 0,
                m["content"],
                m["message_type"],
                1 if m["is_edited"] else 0,
                1 if m["is_deleted"] else 0,
                m["emoji_count"],
                json.dumps(m.get("emojis", [])),
                m["word_count"],
                m["char_count"]
            )
            for m in messages
        ]

        conn.executemany("""
            INSERT INTO messages (
                date_str, time_str, iso_date, iso_datetime, timestamp,
                sender_raw, sender_clean, is_vinu, is_bhumi, is_system,
                content, message_type, is_edited, is_deleted,
                emoji_count, emojis_json, word_count, char_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

    conn.close()
    return len(messages)


def merge_and_insert_messages(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Incrementally merge messages without deleting or duplicating existing records.
    - Accurately identifies new vs already-existing messages
    - Preserves all old messages and associated memory notes
    """
    if not messages:
        return {"total_in_file": 0, "already_existing": 0, "newly_added": 0}

    conn = get_db_connection()
    
    # Map signatures of all existing messages
    existing_rows = conn.execute(
        "SELECT date_str, time_str, sender_clean, content FROM messages"
    ).fetchall()
    
    from collections import Counter
    existing_counts = Counter(
        f"{r['date_str']}||{r['time_str']}||{r['sender_clean']}||{r['content']}"
        for r in existing_rows
    )

    new_messages = []
    already_existing_count = 0

    for m in messages:
        sig = f"{m['date_str']}||{m['time_str']}||{m['sender_clean']}||{m['content']}"
        if existing_counts[sig] > 0:
            existing_counts[sig] -= 1
            already_existing_count += 1
        else:
            new_messages.append(m)

    newly_added_count = len(new_messages)

    if new_messages:
        with conn:
            records = [
                (
                    m["date_str"],
                    m["time_str"],
                    m["iso_date"],
                    m["iso_datetime"],
                    m["timestamp"],
                    m["sender_raw"],
                    m["sender_clean"],
                    1 if m["is_vinu"] else 0,
                    1 if m["is_bhumi"] else 0,
                    1 if m["is_system"] else 0,
                    m["content"],
                    m["message_type"],
                    1 if m["is_edited"] else 0,
                    1 if m["is_deleted"] else 0,
                    m["emoji_count"],
                    json.dumps(m.get("emojis", [])),
                    m["word_count"],
                    m["char_count"]
                )
                for m in new_messages
            ]

            conn.executemany("""
                INSERT INTO messages (
                    date_str, time_str, iso_date, iso_datetime, timestamp,
                    sender_raw, sender_clean, is_vinu, is_bhumi, is_system,
                    content, message_type, is_edited, is_deleted,
                    emoji_count, emojis_json, word_count, char_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)

    conn.close()

    return {
        "total_in_file": len(messages),
        "already_existing": already_existing_count,
        "newly_added": newly_added_count
    }


def clear_all_data():
    """Completely wipe messages, memories, funny flags, and settings."""
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM funny_flags")
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM settings")
        conn.execute("VACUUM")
    conn.close()
