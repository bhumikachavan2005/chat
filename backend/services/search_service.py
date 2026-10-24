"""
Full-Text Search Engine powered by SQLite FTS5
- Sanitized query execution with phrase and keyword support
- Snippet extraction and keyword highlighting
- Embedded conversation context preview for each result
"""

import re
from typing import List, Dict, Any, Optional
from backend.database import get_db_connection
from backend.services.chat_service import format_message_row


def sanitize_fts_query(query: str) -> str:
    """Sanitize user search query for FTS5 syntax."""
    # Strip dangerous characters
    cleaned = re.sub(r'[^\w\s"\'\u0900-\u097F]', ' ', query, flags=re.UNICODE).strip()
    if not cleaned:
        return ""

    tokens = cleaned.split()
    # Format tokens with prefix wildcards for flexible typing
    sanitized_tokens = []
    for token in tokens:
        if token.startswith('"') and token.endswith('"'):
            sanitized_tokens.append(token)
        else:
            clean_token = token.replace('"', '').strip()
            if clean_token:
                sanitized_tokens.append(f'"{clean_token}"*')

    return " ".join(sanitized_tokens)


def search_messages(
    query: str,
    sender: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Search messages using FTS5 with highlighted matches and context."""
    if not query or not query.strip():
        return {"total": 0, "results": []}

    fts_query = sanitize_fts_query(query)
    if not fts_query:
        return {"total": 0, "results": []}

    conn = get_db_connection()
    conditions = ["messages_fts MATCH ?"]
    params = [fts_query]

    if sender:
        if sender.lower() == "vinu":
            conditions.append("m.is_vinu = 1")
        elif sender.lower() == "bhumi":
            conditions.append("m.is_bhumi = 1")
        elif sender.lower() == "system":
            conditions.append("m.is_system = 1")

    if start_date:
        conditions.append("m.iso_date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("m.iso_date <= ?")
        params.append(end_date)

    where_clause = f"WHERE {' AND '.join(conditions)}"

    # Count total matches
    count_query = f"""
        SELECT COUNT(*) as total
        FROM messages_fts fts
        JOIN messages m ON fts.rowid = m.id
        {where_clause}
    """
    try:
        total = conn.execute(count_query, params).fetchone()["total"]
    except Exception:
        # Fallback to standard LIKE if FTS expression fails
        total = 0

    if total == 0:
        # Fallback to LIKE search for partial word / substring matches
        like_term = f"%{query.strip()}%"
        like_conds = ["m.content LIKE ?"]
        like_params = [like_term]
        if sender:
            if sender.lower() == "vinu":
                like_conds.append("m.is_vinu = 1")
            elif sender.lower() == "bhumi":
                like_conds.append("m.is_bhumi = 1")
        if start_date:
            like_conds.append("m.iso_date >= ?")
            like_params.append(start_date)
        if end_date:
            like_conds.append("m.iso_date <= ?")
            like_params.append(end_date)

        where_like = f"WHERE {' AND '.join(like_conds)}"
        total_like = conn.execute(f"SELECT COUNT(*) as total FROM messages m {where_like}", like_params).fetchone()["total"]
        
        search_query = f"""
            SELECT 
                m.*,
                mem.id as memory_id,
                mem.category as memory_category,
                mem.note as memory_note
            FROM messages m
            LEFT JOIN memories mem ON m.id = mem.message_id
            {where_like}
            ORDER BY m.id DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(search_query, like_params + [limit, offset]).fetchall()
    else:
        # FTS5 search with snippet highlight
        search_query = f"""
            SELECT 
                m.*,
                highlight(messages_fts, 0, '<mark class="search-highlight">', '</mark>') as highlighted_content,
                mem.id as memory_id,
                mem.category as memory_category,
                mem.note as memory_note
            FROM messages_fts fts
            JOIN messages m ON fts.rowid = m.id
            LEFT JOIN memories mem ON m.id = mem.message_id
            {where_clause}
            ORDER BY m.id DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(search_query, params + [limit, offset]).fetchall()

    results = []
    for r in rows:
        msg_dict = format_message_row(r)
        if "highlighted_content" in r.keys() and r["highlighted_content"]:
            msg_dict["highlighted_content"] = r["highlighted_content"]
        else:
            # Simple regex highlight fallback
            pattern = re.compile(re.escape(query.strip()), re.IGNORECASE)
            msg_dict["highlighted_content"] = pattern.sub(r'<mark class="search-highlight">\g<0></mark>', msg_dict["content"])

        # Fetch surrounding 1 before and 1 after for context snippet
        ctx_rows = conn.execute("""
            SELECT id, sender_clean, content, time_str, iso_date
            FROM messages
            WHERE id >= ? - 1 AND id <= ? + 1 AND id != ?
            ORDER BY id ASC
        """, (r["id"], r["id"], r["id"])).fetchall()

        msg_dict["context_preview"] = [
            {
                "id": cr["id"],
                "sender_clean": cr["sender_clean"],
                "content": cr["content"],
                "time_str": cr["time_str"],
                "iso_date": cr["iso_date"]
            }
            for cr in ctx_rows
        ]

        results.append(msg_dict)

    conn.close()
    return {
        "query": query,
        "total": total if total > 0 else (total_like if 'total_like' in locals() else 0),
        "limit": limit,
        "offset": offset,
        "results": results
    }
