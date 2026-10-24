"""
Authentication Middleware and Route Guard
"""

from fastapi import Header, HTTPException, status
from typing import Optional
from backend.security.auth import session_store


def require_auth(
    x_archive_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
) -> str:
    """Verify session token from header."""
    token = x_archive_token
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()

    if not token or not session_store.validate_session(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or unauthorized. Please unlock the archive with your password."
        )

    return token
