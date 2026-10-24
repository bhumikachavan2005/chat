"""
Memories Endpoints
- Add, update, delete memory bookmarks
- Category classification and note searching
- Memory statistics
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.api.auth_middleware import require_auth
from backend.services.memory_service import (
    add_memory, update_memory, delete_memory, list_memories, get_memory_stats, VALID_CATEGORIES
)

router = APIRouter(prefix="/api/memories", tags=["memories"], dependencies=[Depends(require_auth)])


class CreateMemoryRequest(BaseModel):
    message_id: int
    category: str = Field(..., description="Category: special, emotional, funny, difficult, birthday, career, friendship, important")
    note: str = ""
    tags: str = ""


class UpdateMemoryRequest(BaseModel):
    category: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[str] = None


@router.get("")
def get_memories(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """List all saved memories with optional category filter or keyword search."""
    return list_memories(category=category, search=search)


@router.get("/stats")
def memory_stats():
    """Get category count breakdown."""
    return get_memory_stats()


@router.post("")
def create_memory(req: CreateMemoryRequest):
    """Attach a memory to a message."""
    cat = req.category.lower()
    if cat not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{req.category}'. Allowed: {', '.join(VALID_CATEGORIES.keys())}"
        )
    return add_memory(
        message_id=req.message_id,
        category=cat,
        note=req.note,
        tags=req.tags
    )


@router.put("/{memory_id}")
def edit_memory(memory_id: int, req: UpdateMemoryRequest):
    """Edit memory notes or category."""
    updated = update_memory(
        memory_id=memory_id,
        category=req.category,
        note=req.note,
        tags=req.tags
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return updated


@router.delete("/{memory_id}")
def remove_memory(memory_id: int):
    """Delete a memory."""
    deleted = delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"status": "success", "message": "Memory removed."}
