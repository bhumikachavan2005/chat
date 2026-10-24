"""
Statistics, Analytics, Timeline & Evolution Endpoints
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from backend.api.auth_middleware import require_auth
from backend.services.stats_service import get_friendship_statistics
from backend.services.timeline_service import get_timeline_tree
from backend.services.evolution_service import compare_evolution

router = APIRouter(prefix="/api/stats", tags=["stats"], dependencies=[Depends(require_auth)])


@router.get("/overview")
def stats_overview():
    """Retrieve comprehensive factual analytics for the archive."""
    return get_friendship_statistics()


@router.get("/timeline")
def timeline_tree():
    """Retrieve hierarchical Year/Month timeline navigation tree."""
    return get_timeline_tree()


@router.get("/evolution")
def friendship_evolution(
    p1_start: Optional[str] = Query(None),
    p1_end: Optional[str] = Query(None),
    p2_start: Optional[str] = Query(None),
    p2_end: Optional[str] = Query(None)
):
    """Compare two distinct friendship time periods."""
    return compare_evolution(
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end
    )
