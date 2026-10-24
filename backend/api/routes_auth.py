"""
Authentication Endpoints
- Setup initial master password
- Unlock / Login session
- Lock / Revoke session
- Change master password
- Lock status and auto-lock configuration
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional
from backend.database import get_setting, set_setting
from backend.security.auth import hash_password, verify_password, session_store
from backend.api.auth_middleware import require_auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SetupRequest(BaseModel):
    password: str = Field(..., min_length=4)


class LoginRequest(BaseModel):
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=4)


class LockSettingsRequest(BaseModel):
    timeout_minutes: int = Field(..., ge=1, le=1440)


@router.get("/status")
def get_auth_status(x_archive_token: Optional[str] = Header(None)):
    """Check whether archive has a password set up and if current session is active."""
    stored_hash = get_setting("password_hash")
    has_password = bool(stored_hash)
    is_authenticated = False
    
    if x_archive_token:
        is_authenticated = session_store.validate_session(x_archive_token)

    timeout_setting = get_setting("auto_lock_minutes", "15")
    try:
        timeout_val = int(timeout_setting)
    except Exception:
        timeout_val = 15

    return {
        "has_password": has_password,
        "is_authenticated": is_authenticated,
        "auto_lock_minutes": timeout_val,
        "archive_title": "Vinu 💝 × Bhumi 🎀"
    }


@router.post("/setup")
def setup_master_password(req: SetupRequest):
    """Set up master password on first launch."""
    existing = get_setting("password_hash")
    if existing:
        raise HTTPException(status_code=400, detail="Master password is already set. Use change-password instead.")

    hashed = hash_password(req.password)
    set_setting("password_hash", hashed)
    set_setting("auto_lock_minutes", "15")

    # Automatically issue session token upon initial setup
    token = session_store.create_session()
    return {
        "status": "success",
        "message": "Archive password created successfully.",
        "token": token
    }


@router.post("/login")
def login(req: LoginRequest):
    """Unlock archive with master password."""
    stored_hash = get_setting("password_hash")
    if not stored_hash:
        raise HTTPException(status_code=400, detail="No password has been set yet. Please set up a password.")

    if not verify_password(stored_hash, req.password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    token = session_store.create_session()
    return {
        "status": "success",
        "message": "Archive unlocked.",
        "token": token
    }


@router.post("/logout")
def logout(x_archive_token: Optional[str] = Header(None)):
    """Lock archive / invalidate session token."""
    if x_archive_token:
        session_store.revoke_session(x_archive_token)
    return {"status": "success", "message": "Archive locked."}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, token: str = Depends(require_auth)):
    """Change the master password."""
    stored_hash = get_setting("password_hash")
    if not stored_hash or not verify_password(stored_hash, req.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    new_hash = hash_password(req.new_password)
    set_setting("password_hash", new_hash)

    # Invalidate all old sessions and keep current user session
    session_store.revoke_all()
    new_token = session_store.create_session()

    return {
        "status": "success",
        "message": "Password updated successfully.",
        "token": new_token
    }


@router.post("/lock-settings")
def update_lock_settings(req: LockSettingsRequest, token: str = Depends(require_auth)):
    """Configure inactivity auto-lock timeout."""
    session_store.set_timeout(req.timeout_minutes)
    set_setting("auto_lock_minutes", str(req.timeout_minutes))
    return {
        "status": "success",
        "timeout_minutes": req.timeout_minutes
    }
