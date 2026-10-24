"""
Friendship Wrapped Endpoints
- Animated story payload
- Secret PIN status, verification, and setup
- Personal photos management and secure file serving
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from backend.api.auth_middleware import require_auth
from backend.services.wrapped_service import generate_friendship_wrapped
from backend.services.wrapped_photo_service import (
    get_wrapped_pin_status, set_wrapped_pin, verify_wrapped_pin,
    save_wrapped_photo, list_wrapped_photos, delete_wrapped_photo, get_photo_filepath
)

router = APIRouter(prefix="/api/wrapped", tags=["wrapped"])


class VerifyPinRequest(BaseModel):
    pin: str


class SetPinRequest(BaseModel):
    pin: str = ""


@router.get("/story", dependencies=[Depends(require_auth)])
def get_wrapped_story():
    """Retrieve structured slides for the Friendship Wrapped animated story."""
    return generate_friendship_wrapped()


@router.get("/pin-status")
def check_pin_status():
    """Check whether a secret PIN is active for Wrapped."""
    return get_wrapped_pin_status()


@router.post("/verify-pin")
def check_pin(req: VerifyPinRequest):
    """Verify the provided secret PIN."""
    is_valid = verify_wrapped_pin(req.pin)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Incorrect Wrapped Secret PIN.")
    return {"status": "success", "unlocked": True}


@router.post("/set-pin")
def configure_pin(req: SetPinRequest):
    """Set, change, or remove the Wrapped PIN."""
    return set_wrapped_pin(req.pin)


@router.get("/photos", dependencies=[Depends(require_auth)])
def get_photos(slide_id: Optional[str] = None):
    """List personal photos uploaded for Wrapped."""
    return list_wrapped_photos(slide_id=slide_id)


@router.post("/photos/upload", dependencies=[Depends(require_auth)])
async def upload_photo(
    file: UploadFile = File(...),
    caption: str = Form(""),
    slide_id: str = Form("moments")
):
    """Upload a personal photo for Wrapped."""
    contents = await file.read()
    if len(contents) > 15 * 1024 * 1024:  # 15MB limit
        raise HTTPException(status_code=400, detail="Image exceeds 15MB maximum size.")

    res = save_wrapped_photo(
        file_bytes=contents,
        original_filename=file.filename or "photo.jpg",
        caption=caption,
        slide_id=slide_id
    )
    return res


@router.delete("/photos/{photo_id}", dependencies=[Depends(require_auth)])
def remove_photo(photo_id: int):
    """Delete an uploaded personal photo."""
    deleted = delete_wrapped_photo(photo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Photo not found.")
    return {"status": "success", "message": "Photo deleted."}


@router.get("/photos/file/{filename}")
def serve_photo_file(filename: str):
    """Serve photo file directly to the browser."""
    path = get_photo_filepath(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Image not found.")
    return FileResponse(path)
