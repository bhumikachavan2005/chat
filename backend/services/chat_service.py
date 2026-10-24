"""
Chat Service
- Message retrieval with pagination
- Surrounding message context for instant search jumping
- Date navigation and bounds
- Joined memory tags
"""

import json
from typing import List, Dict, Any, Optional
from backend.database import get_db_connection


def format_message_row(row) -> Dict[str, Any]:
    """Format SQLite row into a clean dictionary."""
    emojis = []
    if "emojis_json" in row.keys() and row["emojis_json"]:
        try:
            emojis = json.loads(row["emojis_json"])
        except Exception:
            emojis = []

    msg = {
        "id": row["id"],
        "date_str": row["date_str"],
        "time_str": row["time_str"],
        "iso_date": row["iso_date"],
        "iso_datetime": row["iso_datetime"],
        "timestamp": row["timestamp"],
        "sender_raw": row["sender_raw"],
        "sender_clean": row["sender_clean"],
        "is_vinu": bool(row["is_vinu"]),
        "is_bhumi": bool(row["is_bhumi"]),
        "is_system": bool(row["is_system"]),
        "content": row["content"],
        "message_type": row["message_type"],
        "is_edited": bool(row["is_edited"]),
        "is_deleted": bool(row["is_deleted"]),
        "emoji_count": row["emoji_count"],
        "emojis": emojis,
        "word_count": row["word_count"],
        "char_count": row["char_count"]
    }

    if "memory_id" in row.keys() and row["memory_id"]:
        category = row["memory_category"] if "memory_category" in row.keys() else (row["category"] if "category" in row.keys() else "")
        note = row["memory_note"] if "memory_note" in row.keys() else (row["note"] if "note" in row.keys() else "")
        msg["memory"] = {
            "id": row["memory_id"],
            "category": category,
            "note": note
        }
    else:
        msg["memory"] = None

    return msg


def get_message_by_id(message_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single message by ID with its attached memory."""
    conn = get_db_connection()
    query = """
        SELECT 
            m.*,
            mem.id as memory_id,
            mem.category as memory_category,
            mem.note as memory_note
        FROM messages m
        LEFT JOIN memories mem ON m.id = mem.message_id
        WHERE m.id = ?
    """
    row = conn.execute(query, (message_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return format_message_row(row)


def get_messages(
    limit: int = 100,
    offset: int = 0,
    sender: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    media_only: bool = False,
    memories_only: bool = False,
    preset: Optional[str] = None,
    sort: str = "asc"
) -> Dict[str, Any]:
    """Retrieve filtered and paginated chat messages."""
    conn = get_db_connection()
    conditions = []
    params = []

    if sender:
        if sender.lower() == "vinu":
            conditions.append("m.is_vinu = 1")
        elif sender.lower() in ["bhumi", "bhuu", "bhumika"]:
            conditions.append("(m.is_bhumi = 1 OR m.sender_clean LIKE '%Bhuu%')")
        elif sender.lower() == "system":
            conditions.append("m.is_system = 1")

    if start_date:
        conditions.append("m.iso_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("m.iso_date <= ?")
        params.append(end_date)

    if media_only:
        conditions.append("m.message_type IN ('media', 'call')")

    if memories_only:
        conditions.append("mem.id IS NOT NULL")

    if preset:
        if preset == "late_night":
            conditions.append("(m.time_str LIKE '%11:%pm' OR m.time_str LIKE '%12:%am' OR m.time_str LIKE '%1:%am' OR m.time_str LIKE '%2:%am' OR m.time_str LIKE '%3:%am' OR m.time_str LIKE '%4:%am')")
        elif preset == "long_messages":
            conditions.append("m.word_count >= 25")
        elif preset == "calls":
            conditions.append("m.message_type = 'call'")
        elif preset == "deleted":
            conditions.append("m.is_deleted = 1")
        elif preset == "voice":
            conditions.append("m.content LIKE '%.opus%'")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order = "ASC" if sort.lower() == "asc" else "DESC"

    # Count total matching
    count_query = f"""
        SELECT COUNT(*) as total
        FROM messages m
        LEFT JOIN memories mem ON m.id = mem.message_id
        {where_clause}
    """
    total = conn.execute(count_query, params).fetchone()["total"]

    # Fetch rows
    fetch_query = f"""
        SELECT 
            m.*,
            mem.id as memory_id,
            mem.category as memory_category,
            mem.note as memory_note
        FROM messages m
        LEFT JOIN memories mem ON m.id = mem.message_id
        {where_clause}
        ORDER BY m.id {order}
        LIMIT ? OFFSET ?
    """
    rows = conn.execute(fetch_query, params + [limit, offset]).fetchall()
    conn.close()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "messages": [format_message_row(r) for r in rows]
    }


def get_message_context(message_id: int, context_size: int = 10) -> Dict[str, Any]:
    """Get target message with surrounding conversation messages."""
    conn = get_db_connection()
    
    # Check if target exists
    target = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    if not target:
        conn.close()
        return {"target": None, "messages": [], "target_index": 0}

    # Fetch context before and after
    query = f"""
        SELECT 
            m.*,
            mem.id as memory_id,
            mem.category as memory_category,
            mem.note as memory_note
        FROM messages m
        LEFT JOIN memories mem ON m.id = mem.message_id
        WHERE m.id >= ? - ? AND m.id <= ? + ?
        ORDER BY m.id ASC
    """
    rows = conn.execute(query, (message_id, context_size, message_id, context_size)).fetchall()
    
    # Calculate overall index of target
    target_index = conn.execute("SELECT COUNT(*) as idx FROM messages WHERE id < ?", (message_id,)).fetchone()["idx"]
    conn.close()

    return {
        "target_id": message_id,
        "target_index": target_index,
        "messages": [format_message_row(r) for r in rows]
    }


def get_chat_bounds() -> Dict[str, Any]:
    """Get earliest and latest date, and total message counts."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT 
            COUNT(*) as total_count,
            MIN(iso_date) as start_date,
            MAX(iso_date) as end_date,
            MIN(id) as first_id,
            MAX(id) as last_id
        FROM messages
    """).fetchone()
    conn.close()

    if not row or row["total_count"] == 0:
        return {
            "total_count": 0,
            "start_date": None,
            "end_date": None,
            "first_id": None,
            "last_id": None
        }

    return {
        "total_count": row["total_count"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "first_id": row["first_id"],
        "last_id": row["last_id"]
    }


def find_message_by_date(iso_date: str) -> Optional[int]:
    """Find the message ID closest to or on the given ISO date."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT id FROM messages WHERE iso_date >= ? ORDER BY id ASC LIMIT 1
    """, (iso_date,)).fetchone()
    conn.close()
    return row["id"] if row else None


def get_message_offset(
    message_id: int,
    sender: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    media_only: bool = False,
    memories_only: bool = False,
    preset: Optional[str] = None
) -> int:
    """Find the 0-indexed position (offset) of a message within the current filtered query."""
    conn = get_db_connection()
    conditions = []
    params = []

    if sender:
        if sender.lower() == "vinu":
            conditions.append("m.is_vinu = 1")
        elif sender.lower() in ["bhumi", "bhuu", "bhumika"]:
            conditions.append("(m.is_bhumi = 1 OR m.sender_clean LIKE '%Bhuu%')")
        elif sender.lower() == "system":
            conditions.append("m.is_system = 1")

    if start_date:
        conditions.append("m.iso_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("m.iso_date <= ?")
        params.append(end_date)

    if media_only:
        conditions.append("m.message_type IN ('media', 'call')")

    if memories_only:
        conditions.append("mem.id IS NOT NULL")

    if preset:
        if preset == "late_night":
            conditions.append("(m.time_str LIKE '%11:%pm' OR m.time_str LIKE '%12:%am' OR m.time_str LIKE '%1:%am' OR m.time_str LIKE '%2:%am' OR m.time_str LIKE '%3:%am' OR m.time_str LIKE '%4:%am')")
        elif preset == "long_messages":
            conditions.append("m.word_count >= 25")
        elif preset == "calls":
            conditions.append("m.message_type = 'call'")
        elif preset == "deleted":
            conditions.append("m.is_deleted = 1")
        elif preset == "voice":
            conditions.append("m.content LIKE '%.opus%'")

    conditions.append("m.id < ?")
    params.append(message_id)

    where_clause = f"WHERE {' AND '.join(conditions)}"
    query = f"""
        SELECT COUNT(*) as idx
        FROM messages m
        LEFT JOIN memories mem ON m.id = mem.message_id
        {where_clause}
    """
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row["idx"] if row else 0


def get_day_stats(iso_date: str) -> Dict[str, Any]:
    """Get message count and sender breakdown for a specific date."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_vinu = 1 THEN 1 ELSE 0 END) as vinu_count,
            SUM(CASE WHEN is_bhumi = 1 OR sender_clean LIKE '%Bhuu%' THEN 1 ELSE 0 END) as bhumi_count
        FROM messages WHERE iso_date = ?
    """, (iso_date,)).fetchone()
    conn.close()
    return {
        "iso_date": iso_date,
        "total": row["total"] if row and row["total"] else 0,
        "vinu_count": row["vinu_count"] if row and row["vinu_count"] else 0,
        "bhumi_count": row["bhumi_count"] if row and row["bhumi_count"] else 0
    }


def get_random_message() -> Optional[Dict[str, Any]]:
    """Retrieve a random meaningful message with context."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT id FROM messages 
        WHERE is_system = 0 AND word_count > 3 AND message_type = 'text'
        ORDER BY RANDOM() LIMIT 1
    """).fetchone()
    conn.close()
    if row:
        return get_message_context(row["id"], context_size=5)
    return None


