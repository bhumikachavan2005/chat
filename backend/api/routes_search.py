"""
Search Endpoints
- FTS5 keyword and phrase search
- Highlighted snippets
- Conversation preview context
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from backend.api.auth_middleware import require_auth
from backend.services.search_service import search_messages

router = APIRouter(prefix="/api/search", tags=["search"], dependencies=[Depends(require_auth)])


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    sender: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Execute full-text search across all messages."""
    return search_messages(
        query=q,
        sender=sender,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
