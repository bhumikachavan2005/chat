"""
Chat Endpoints
- Paginated message retrieval
- Filtering by sender, date range, media, and memories
- Surrounding message context
- Date navigation bounds
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from backend.api.auth_middleware import require_auth
from backend.services.chat_service import (
    get_messages, get_message_context, get_chat_bounds, find_message_by_date, 
    get_random_message, get_message_offset, get_day_stats, get_message_by_id
)

router = APIRouter(prefix="/api/chat", tags=["chat"], dependencies=[Depends(require_auth)])


@router.get("/message/{message_id}")
def single_message(message_id: int):
    """Retrieve a single message with its attached memory."""
    msg = get_message_by_id(message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")
    return msg


@router.get("/random")
def random_message():
    """Retrieve a random memory/message with surrounding context."""
    res = get_random_message()
    if not res:
        raise HTTPException(status_code=404, detail="No messages available.")
    return res


@router.get("/bounds")
def chat_bounds():
    """Retrieve chat date range and overall message count."""
    return get_chat_bounds()


@router.get("/messages")
def list_messages(
    limit: int = Query(250, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    sender: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    media_only: bool = Query(False),
    memories_only: bool = Query(False),
    preset: Optional[str] = Query(None),
    sort: str = Query("asc")
):
    """Get paginated messages with filters."""
    return get_messages(
        limit=limit,
        offset=offset,
        sender=sender,
        start_date=start_date,
        end_date=end_date,
        media_only=media_only,
        memories_only=memories_only,
        preset=preset,
        sort=sort
    )


@router.get("/around/{message_id}")
def message_context(message_id: int, context_size: int = Query(15, ge=0, le=50)):
    """Retrieve target message and surrounding conversation context."""
    res = get_message_context(message_id, context_size=context_size)
    if not res["target_id"]:
        raise HTTPException(status_code=404, detail="Message not found.")
    return res


@router.get("/jump-date")
def jump_to_date(date: str = Query(..., pattern=r'^\d{4}-\d{2}-\d{2}$')):
    """Find closest message ID and offset for a given ISO date (YYYY-MM-DD)."""
    msg_id = find_message_by_date(date)
    if not msg_id:
        raise HTTPException(status_code=404, detail="No messages found on or after this date.")
    offset = get_message_offset(msg_id)
    day_stats = get_day_stats(date)
    return {"iso_date": date, "message_id": msg_id, "offset": offset, "day_stats": day_stats}


@router.get("/offset/{message_id}")
def get_offset_of_message(
    message_id: int,
    sender: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    media_only: bool = Query(False),
    memories_only: bool = Query(False),
    preset: Optional[str] = Query(None)
):
    """Find the offset index of a message under current filters."""
    offset = get_message_offset(
        message_id=message_id,
        sender=sender,
        start_date=start_date,
        end_date=end_date,
        media_only=media_only,
        memories_only=memories_only,
        preset=preset
    )
    return {"message_id": message_id, "offset": offset}

