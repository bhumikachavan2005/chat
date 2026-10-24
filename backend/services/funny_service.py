"""
Funny Moments Service
- Detects humor signals (😂, 🤣, 😭, 💀, haha, lol)
- Groups messages with surrounding conversation context
- Allows user confirmation or dismissal
"""

import re
from typing import List, Dict, Any, Optional
from backend.database import get_db_connection
from backend.services.chat_service import format_message_row

FUNNY_SIGNALS_REGEX = re.compile(
    r'(😂|🤣|💀|😭|(?:\b(?:ha){2,}\b)|(?:\b(?:he){2,}\b)|(?:\b(?:ja){2,}\b)|\blol\b|\blmao\b|\brofl\b)',
    re.IGNORECASE | re.UNICODE
)


def get_funny_moments(status: Optional[str] = None, limit: int = 40) -> List[Dict[str, Any]]:
    """Retrieve messages with detected humor signals and conversation snippets."""
    conn = get_db_connection()

    # Query candidate messages containing funny emojis or laugh words
    query = """
        SELECT 
            m.*,
            ff.id as flag_id,
            ff.status as flag_status,
            ff.signals as flag_signals,
            mem.id as memory_id,
            mem.category as memory_category,
            mem.note as memory_note
        FROM messages m
        LEFT JOIN funny_flags ff ON m.id = ff.message_id
        LEFT JOIN memories mem ON m.id = mem.message_id
        WHERE (
            m.content LIKE '%😂%' OR 
            m.content LIKE '%🤣%' OR 
            m.content LIKE '%💀%' OR 
            m.content LIKE '%haha%' OR 
            m.content LIKE '%hahaha%' OR 
            m.content LIKE '%lol%'
        ) AND m.message_type = 'text'
    """
    
    if status == "confirmed":
        query += " AND ff.status = 'confirmed'"
    elif status == "dismissed":
        query += " AND ff.status = 'dismissed'"
    elif status == "suggested":
        query += " AND (ff.status IS NULL OR ff.status = 'suggested')"
    else:
        # Default: show non-dismissed
        query += " AND (ff.status IS NULL OR ff.status != 'dismissed')"

    query += " ORDER BY m.id DESC LIMIT ?"
    rows = conn.execute(query, (limit,)).fetchall()

    moments = []
    for r in rows:
        signals = FUNNY_SIGNALS_REGEX.findall(r["content"])
        unique_signals = list(set([s.lower() for s in signals]))
        
        # Fetch 2 messages before and 2 messages after for full context
        ctx_rows = conn.execute("""
            SELECT id, sender_clean, content, time_str, iso_date, is_vinu, is_bhumi
            FROM messages
            WHERE id >= ? - 2 AND id <= ? + 2
            ORDER BY id ASC
        """, (r["id"], r["id"])).fetchall()

        moments.append({
            "message_id": r["id"],
            "flag_id": r["flag_id"],
            "status": r["flag_status"] or "suggested",
            "signals": unique_signals,
            "target_message": format_message_row(r),
            "context_thread": [
                {
                    "id": cr["id"],
                    "sender_clean": cr["sender_clean"],
                    "content": cr["content"],
                    "time_str": cr["time_str"],
                    "iso_date": cr["iso_date"],
                    "is_vinu": bool(cr["is_vinu"]),
                    "is_bhumi": bool(cr["is_bhumi"]),
                    "is_target": cr["id"] == r["id"]
                }
                for cr in ctx_rows
            ]
        })

    conn.close()
    return moments


def set_funny_status(message_id: int, status: str) -> bool:
    """Set confirmation/dismissal status for a funny moment."""
    valid_statuses = ["suggested", "confirmed", "dismissed"]
    if status not in valid_statuses:
        return False

    conn = get_db_connection()
    with conn:
        conn.execute("""
            INSERT INTO funny_flags (message_id, status)
            VALUES (?, ?)
            ON CONFLICT(message_id) DO UPDATE SET status = excluded.status
        """, (message_id, status))
    conn.close()
    return True
