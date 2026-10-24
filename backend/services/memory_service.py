"""
Memory System Service
- Add, update, delete, and list memories
- Category classification and filtering
- Joins original message content and timestamp
"""

import time
from typing import List, Dict, Any, Optional
from backend.database import get_db_connection
from backend.services.chat_service import format_message_row

VALID_CATEGORIES = {
    "special": {"label": "Special", "emoji": "❤️", "color": "#ef4444"},
    "emotional": {"label": "Emotional", "emoji": "🥹", "color": "#ec4899"},
    "funny": {"label": "Funny", "emoji": "😂", "color": "#f59e0b"},
    "difficult": {"label": "Difficult", "emoji": "😭", "color": "#6366f1"},
    "birthday": {"label": "Birthday", "emoji": "🎂", "color": "#8b5cf6"},
    "career": {"label": "Career", "emoji": "🎓", "color": "#3b82f6"},
    "friendship": {"label": "Friendship", "emoji": "🫂", "color": "#10b981"},
    "important": {"label": "Important", "emoji": "⭐", "color": "#eab308"}
}


def add_memory(message_id: int, category: str, note: str = "", tags: str = "") -> Dict[str, Any]:
    """Add or update a memory attached to a message (guarantees NO duplicate memories for the same message)."""
    cat = category.lower() if category.lower() in VALID_CATEGORIES else "special"
    created_at = int(time.time())
    
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM memories WHERE message_id = ?", (message_id,)).fetchone()
    
    with conn:
        if existing:
            memory_id = existing["id"]
            conn.execute("""
                UPDATE memories 
                SET category = ?, note = ?, tags = ? 
                WHERE id = ?
            """, (cat, note.strip(), tags.strip(), memory_id))
        else:
            cursor = conn.execute("""
                INSERT INTO memories (message_id, category, note, tags, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (message_id, cat, note.strip(), tags.strip(), created_at))
            memory_id = cursor.lastrowid
    conn.close()

    return get_memory_by_id(memory_id)


def update_memory(memory_id: int, category: Optional[str] = None, note: Optional[str] = None, tags: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update an existing memory."""
    conn = get_db_connection()
    fields = []
    params = []

    if category is not None:
        cat = category.lower() if category.lower() in VALID_CATEGORIES else "special"
        fields.append("category = ?")
        params.append(cat)

    if note is not None:
        fields.append("note = ?")
        params.append(note.strip())

    if tags is not None:
        fields.append("tags = ?")
        params.append(tags.strip())

    if not fields:
        conn.close()
        return get_memory_by_id(memory_id)

    params.append(memory_id)
    with conn:
        conn.execute(f"UPDATE memories SET {', '.join(fields)} WHERE id = ?", params)
    conn.close()

    return get_memory_by_id(memory_id)


def delete_memory(memory_id: int) -> bool:
    """Delete a memory."""
    conn = get_db_connection()
    with conn:
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_memory_by_id(memory_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve memory with its attached message details."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT 
            mem.id as memory_id,
            mem.category,
            mem.note,
            mem.tags,
            mem.created_at as memory_created_at,
            m.*
        FROM memories mem
        JOIN messages m ON mem.message_id = m.id
        WHERE mem.id = ?
    """, (memory_id,)).fetchone()
    conn.close()

    if not row:
        return None

    cat_meta = VALID_CATEGORIES.get(row["category"], VALID_CATEGORIES["special"])
    return {
        "id": row["memory_id"],
        "message_id": row["id"],
        "category": row["category"],
        "category_label": cat_meta["label"],
        "category_emoji": cat_meta["emoji"],
        "category_color": cat_meta["color"],
        "note": row["note"],
        "tags": row["tags"],
        "created_at": row["memory_created_at"],
        "message": format_message_row(row)
    }


def list_memories(category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """List memories with optional category filter or text search."""
    conn = get_db_connection()
    conditions = []
    params = []

    if category and category.lower() in VALID_CATEGORIES:
        conditions.append("mem.category = ?")
        params.append(category.lower())

    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append("(mem.note LIKE ? OR m.content LIKE ? OR mem.tags LIKE ?)")
        params.extend([term, term, term])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT 
            mem.id as memory_id,
            mem.category,
            mem.note,
            mem.tags,
            mem.created_at as memory_created_at,
            m.*
        FROM memories mem
        JOIN messages m ON mem.message_id = m.id
        {where}
        ORDER BY m.timestamp DESC
    """
    rows = conn.execute(query, params).fetchall()
    conn.close()

    memories = []
    for r in rows:
        cat_meta = VALID_CATEGORIES.get(r["category"], VALID_CATEGORIES["special"])
        memories.append({
            "id": r["memory_id"],
            "message_id": r["id"],
            "category": r["category"],
            "category_label": cat_meta["label"],
            "category_emoji": cat_meta["emoji"],
            "category_color": cat_meta["color"],
            "note": r["note"],
            "tags": r["tags"],
            "created_at": r["memory_created_at"],
            "message": format_message_row(r)
        })

    return memories


def get_memory_stats() -> Dict[str, Any]:
    """Get category counts and summary."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT category, COUNT(*) as count
        FROM memories
        GROUP BY category
    """).fetchall()
    conn.close()

    counts = {k: 0 for k in VALID_CATEGORIES}
    total = 0
    for r in rows:
        cat = r["category"]
        if cat in counts:
            counts[cat] = r["count"]
            total += r["count"]

    categories_list = []
    for k, v in VALID_CATEGORIES.items():
        categories_list.append({
            "key": k,
            "label": v["label"],
            "emoji": v["emoji"],
            "color": v["color"],
            "count": counts[k]
        })

    return {
        "total": total,
        "categories": categories_list,
        "counts": counts
    }
