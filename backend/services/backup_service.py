"""
Secure AES-256-GCM Backup, Restore & Incremental TXT Import Service
- Preserves existing bookmarks/memories across re-imports
- Authenticated AES-256-GCM encrypted database export and restore
- Auto-reindexes FTS5 search and re-computes all statistics on import
"""

import json
import time
from typing import Dict, Any, List
from backend.database import get_db_connection, bulk_insert_messages
from backend.parser.whatsapp_parser import parse_whatsapp_text
from backend.security.auth import encrypt_data_aes_gcm, decrypt_data_aes_gcm


def export_encrypted_backup(passphrase: str) -> bytes:
    """Generate AES-256-GCM encrypted backup of all messages, memories, and settings."""
    conn = get_db_connection()

    messages = [dict(r) for r in conn.execute("SELECT * FROM messages ORDER BY id ASC").fetchall()]
    memories = [dict(r) for r in conn.execute("SELECT * FROM memories ORDER BY id ASC").fetchall()]
    funny_flags = [dict(r) for r in conn.execute("SELECT * FROM funny_flags ORDER BY id ASC").fetchall()]
    settings = [dict(r) for r in conn.execute("SELECT * FROM settings").fetchall()]

    conn.close()

    payload = {
        "version": "1.0",
        "created_at": int(time.time()),
        "messages_count": len(messages),
        "memories_count": len(memories),
        "messages": messages,
        "memories": memories,
        "funny_flags": funny_flags,
        "settings": settings
    }

    json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return encrypt_data_aes_gcm(json_bytes, passphrase)


def restore_encrypted_backup(encrypted_bytes: bytes, passphrase: str) -> Dict[str, Any]:
    """Decrypt and restore database from authenticated backup."""
    decrypted_bytes = decrypt_data_aes_gcm(encrypted_bytes, passphrase)
    payload = json.loads(decrypted_bytes.decode("utf-8"))

    messages = payload.get("messages", [])
    memories = payload.get("memories", [])
    funny_flags = payload.get("funny_flags", [])

    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM funny_flags")
        conn.execute("DELETE FROM messages")

        if messages:
            cols = [
                "id", "date_str", "time_str", "iso_date", "iso_datetime", "timestamp",
                "sender_raw", "sender_clean", "is_vinu", "is_bhumi", "is_system",
                "content", "message_type", "is_edited", "is_deleted",
                "emoji_count", "emojis_json", "word_count", "char_count"
            ]
            placeholders = ", ".join(["?"] * len(cols))
            records = [
                tuple(m.get(c) for c in cols)
                for m in messages
            ]
            conn.executemany(f"INSERT INTO messages ({', '.join(cols)}) VALUES ({placeholders})", records)

        if memories:
            for mem in memories:
                conn.execute("""
                    INSERT INTO memories (id, message_id, category, note, tags, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (mem.get("id"), mem["message_id"], mem["category"], mem.get("note", ""), mem.get("tags", ""), mem.get("created_at", int(time.time()))))

        if funny_flags:
            for ff in funny_flags:
                conn.execute("""
                    INSERT INTO funny_flags (id, message_id, status, signals)
                    VALUES (?, ?, ?, ?)
                """, (ff.get("id"), ff["message_id"], ff.get("status", "suggested"), ff.get("signals", "")))

    conn.close()

    return {
        "status": "success",
        "restored_messages": len(messages),
        "restored_memories": len(memories),
        "restored_funny_flags": len(funny_flags)
    }


def import_txt_content(raw_text: str) -> Dict[str, Any]:
    """
    Parse and incrementally import raw WhatsApp export text.
    - Lossless: NEVER deletes or modifies existing messages or saved memories.
    - Deduplicates: Skips messages that already exist in the archive.
    - Appends: Only inserts new messages from the export file.
    - Auto-reindexes FTS5 search and triggers immediate stats/wrapped refresh.
    """
    parsed_msgs = parse_whatsapp_text(raw_text)
    if not parsed_msgs:
        return {"imported_count": 0, "message": "No valid messages found in text."}

    from backend.database import merge_and_insert_messages
    merge_result = merge_and_insert_messages(parsed_msgs)

    conn = get_db_connection()
    total_in_db = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
    total_memories = conn.execute("SELECT COUNT(*) as c FROM memories").fetchone()["c"]
    conn.close()

    newly_added = merge_result["newly_added"]
    already_existing = merge_result["already_existing"]

    if newly_added > 0:
        msg = f"Added {newly_added:,} new messages ({already_existing:,} existing messages retained). Total archive is now {total_in_db:,} messages with {total_memories} preserved memories."
    else:
        msg = f"All {already_existing:,} messages from this export are already in the archive. 0 duplicates added."

    return {
        "status": "success",
        "imported_count": newly_added,
        "already_existing": already_existing,
        "total_messages": total_in_db,
        "preserved_memories": total_memories,
        "message": msg
    }
