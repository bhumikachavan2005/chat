"""
Private Offline Insights & Funny Moments Endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.api.auth_middleware import require_auth
from backend.services.insights_service import (
    PREBUILT_INSIGHTS, get_insight_by_id, resolve_custom_query
)
from backend.services.funny_service import (
    get_funny_moments, set_funny_status
)

router = APIRouter(tags=["insights"], dependencies=[Depends(require_auth)])


class CustomQueryRequest(BaseModel):
    query: str = Field(..., min_length=2)


class FunnyStatusRequest(BaseModel):
    message_id: int
    status: str = Field(..., description="suggested, confirmed, dismissed")


@router.get("/api/insights/prebuilt")
def list_prebuilt_insights():
    """List available prebuilt offline inquiry topics."""
    return {"insights": PREBUILT_INSIGHTS}


@router.get("/api/insights/query/{insight_id}")
def query_insight(insight_id: str):
    """Execute prebuilt insight analysis with message citations."""
    return get_insight_by_id(insight_id)


@router.post("/api/insights/ask")
def ask_custom_question(req: CustomQueryRequest):
    """Answer factual search inquiries 100% offline from local database."""
    return resolve_custom_query(req.query)


@router.get("/api/funny/moments")
def list_funny_moments(
    status: Optional[str] = Query(None),
    limit: int = Query(40, ge=1, le=100)
):
    """Retrieve funny detected snippets and context thread."""
    return {"moments": get_funny_moments(status=status, limit=limit)}


@router.post("/api/funny/status")
def update_funny_status(req: FunnyStatusRequest):
    """Confirm or dismiss a suggested funny moment."""
    success = set_funny_status(req.message_id, req.status)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid funny status. Allowed: suggested, confirmed, dismissed")
    return {"status": "success", "message_id": req.message_id, "new_status": req.status}
