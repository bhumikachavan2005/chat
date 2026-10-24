"""
Wrapped Photo & PIN Management Service
- Secure storage of personal friendship photos for Wrapped presentation
- PIN protection and verification for Wrapped
"""

import os
import time
import uuid
import mimetypes
from typing import List, Dict, Any, Optional
from backend.database import get_db_connection, get_setting, set_setting, WRAPPED_PHOTOS_DIR
from backend.security.auth import hash_password, verify_password

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def get_wrapped_pin_status() -> Dict[str, Any]:
    """Check if a secret PIN has been configured for Wrapped."""
    pin_hash = get_setting("wrapped_pin_hash")
    return {
        "has_pin": bool(pin_hash)
    }


def set_wrapped_pin(pin: str) -> Dict[str, Any]:
    """Set, change, or remove the Wrapped PIN."""
    pin_clean = pin.strip() if pin else ""
    conn = get_db_connection()
    if pin_clean:
        hashed = hash_password(pin_clean)
        set_setting("wrapped_pin_hash", hashed)
        return {"status": "success", "message": "Wrapped Secret PIN set successfully!", "has_pin": True}
    else:
        # Remove PIN if empty string passed
        with conn:
            conn.execute("DELETE FROM settings WHERE key = 'wrapped_pin_hash'")
        conn.close()
        return {"status": "success", "message": "Wrapped PIN protection removed.", "has_pin": False}


def verify_wrapped_pin(pin: str) -> bool:
    """Verify the provided PIN against the stored hash."""
    pin_hash = get_setting("wrapped_pin_hash")
    if not pin_hash:
        return True  # If no PIN configured, always allowed
    return verify_password(pin_hash, pin.strip())


def save_wrapped_photo(file_bytes: bytes, original_filename: str, caption: str = "", slide_id: str = "moments") -> Dict[str, Any]:
    """Save an uploaded image file and insert record into database."""
    _, ext = os.path.splitext(original_filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"

    unique_filename = f"photo_{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs(WRAPPED_PHOTOS_DIR, exist_ok=True)
    file_path = os.path.join(WRAPPED_PHOTOS_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    created_at = int(time.time())
    caption_clean = caption.strip()
    slide_id_clean = slide_id.strip() if slide_id else "moments"

    conn = get_db_connection()
    with conn:
        cursor = conn.execute("""
            INSERT INTO wrapped_photos (filename, caption, slide_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (unique_filename, caption_clean, slide_id_clean, created_at))
        photo_id = cursor.lastrowid
    conn.close()

    return {
        "id": photo_id,
        "filename": unique_filename,
        "url": f"/api/wrapped/photos/file/{unique_filename}",
        "caption": caption_clean,
        "slide_id": slide_id_clean,
        "created_at": created_at
    }


def list_wrapped_photos(slide_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all personal photos uploaded for Wrapped."""
    conn = get_db_connection()
    if slide_id:
        rows = conn.execute("""
            SELECT * FROM wrapped_photos WHERE slide_id = ? ORDER BY id ASC
        """, (slide_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM wrapped_photos ORDER BY id ASC
        """).fetchall()
    conn.close()

    photos = []
    for r in rows:
        photos.append({
            "id": r["id"],
            "filename": r["filename"],
            "url": f"/api/wrapped/photos/file/{r['filename']}",
            "caption": r["caption"] or "",
            "slide_id": r["slide_id"] or "moments",
            "created_at": r["created_at"]
        })
    return photos


def delete_wrapped_photo(photo_id: int) -> bool:
    """Delete a photo record and its file from disk."""
    conn = get_db_connection()
    row = conn.execute("SELECT filename FROM wrapped_photos WHERE id = ?", (photo_id,)).fetchone()
    if not row:
        conn.close()
        return False

    filename = row["filename"]
    with conn:
        cursor = conn.execute("DELETE FROM wrapped_photos WHERE id = ?", (photo_id,))
        deleted = cursor.rowcount > 0
    conn.close()

    file_path = os.path.join(WRAPPED_PHOTOS_DIR, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    return deleted


def get_photo_filepath(filename: str) -> Optional[str]:
    """Get absolute path to safe photo file."""
    clean_name = os.path.basename(filename)
    path = os.path.join(WRAPPED_PHOTOS_DIR, clean_name)
    if os.path.exists(path) and os.path.isfile(path):
        return path
    return None
