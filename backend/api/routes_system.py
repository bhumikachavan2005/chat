"""
System, Backup, Export/Import, and Data Lifecycle Endpoints
"""

import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from pydantic import BaseModel
from backend.api.auth_middleware import require_auth
from backend.database import get_setting, clear_all_data
from backend.security.auth import verify_password
from backend.services.backup_service import (
    export_encrypted_backup, restore_encrypted_backup, import_txt_content
)

router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[Depends(require_auth)])


class ExportRequest(BaseModel):
    passphrase: str


class WipeRequest(BaseModel):
    password: str


@router.post("/export-backup")
def export_backup(req: ExportRequest):
    """Generate AES-256-GCM encrypted backup file."""
    if not req.passphrase or len(req.passphrase) < 4:
        raise HTTPException(status_code=400, detail="Backup passphrase must be at least 4 characters long.")

    try:
        enc_bytes = export_encrypted_backup(req.passphrase)
        filename = f"vinu_bhumi_archive_backup_{int(time.time())}.enc"
        return Response(
            content=enc_bytes,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate backup: {str(e)}")


@router.post("/restore-backup")
async def restore_backup(
    file: UploadFile = File(...),
    passphrase: str = Form(...)
):
    """Restore database from AES-256-GCM encrypted backup file."""
    try:
        content = await file.read()
        res = restore_encrypted_backup(content, passphrase)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption or restore failed: {str(e)}")


@router.post("/import-txt")
async def import_txt(file: UploadFile = File(...)):
    """Parse and import raw WhatsApp TXT export file."""
    try:
        content_bytes = await file.read()
        raw_text = content_bytes.decode('utf-8', errors='replace')
        res = import_txt_content(raw_text)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


@router.post("/wipe-all")
def wipe_all_data(req: WipeRequest):
    """Nuclear wipe of all chat data, memories, and settings."""
    stored_hash = get_setting("password_hash")
    if not stored_hash or not verify_password(stored_hash, req.password):
        raise HTTPException(status_code=400, detail="Incorrect password. Wipe aborted.")

    clear_all_data()
    return {"status": "success", "message": "All chat records and settings have been completely erased."}
