"""
Security & Authentication Engine
- Argon2id password hashing with Scrypt fallback
- Ephemeral cryptographic session token manager
- Configurable auto-lock inactivity timer
- AES-256-GCM authenticated encryption for private backups
"""

import time
import secrets
import base64
import os
from typing import Optional, Dict, Any

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    HAS_ARGON2 = True
    _argon2_hasher = PasswordHasher(
        time_cost=2,
        memory_cost=65536,
        parallelism=2,
        hash_len=32
    )
except ImportError:
    HAS_ARGON2 = False

import hashlib

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# Password Hashing Functions
def hash_password(password: str) -> str:
    """Hash a password securely using Argon2id or Scrypt."""
    if HAS_ARGON2:
        return _argon2_hasher.hash(password)
    else:
        # Fallback to Scrypt
        salt = secrets.token_bytes(16)
        h = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=16384, r=8, p=1)
        return f"scrypt${base64.b64encode(salt).decode('utf-8')}${base64.b64encode(h).decode('utf-8')}"


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password against stored hash without leaking timing info."""
    if not stored_hash or not password:
        return False

    if stored_hash.startswith("scrypt$"):
        try:
            parts = stored_hash.split("$")
            salt = base64.b64decode(parts[1])
            expected = base64.b64decode(parts[2])
            computed = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=16384, r=8, p=1)
            return secrets.compare_digest(expected, computed)
        except Exception:
            return False
    elif HAS_ARGON2:
        try:
            return _argon2_hasher.verify(stored_hash, password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False
    return False


# In-Memory Session Token Manager
class SessionStore:
    def __init__(self, default_timeout_minutes: int = 15):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout_seconds = default_timeout_minutes * 60

    def set_timeout(self, minutes: int):
        self.timeout_seconds = max(60, minutes * 60)

    def get_timeout_minutes(self) -> int:
        return int(self.timeout_seconds // 60)

    def create_session(self) -> str:
        """Create a new authenticated session token."""
        token = secrets.token_urlsafe(32)
        now = time.time()
        self.sessions[token] = {
            "created_at": now,
            "last_active": now
        }
        return token

    def validate_session(self, token: Optional[str]) -> bool:
        """Validate if session token exists and has not timed out due to inactivity."""
        if not token or token not in self.sessions:
            return False

        sess = self.sessions[token]
        now = time.time()
        if now - sess["last_active"] > self.timeout_seconds:
            # Session expired due to inactivity
            del self.sessions[token]
            return False

        # Refresh activity timestamp
        sess["last_active"] = now
        return True

    def revoke_session(self, token: Optional[str]) -> bool:
        """Revoke a session (logout/lock)."""
        if token and token in self.sessions:
            del self.sessions[token]
            return True
        return False

    def revoke_all(self):
        """Nuclear lock of all sessions."""
        self.sessions.clear()


# Global in-memory session manager instance
session_store = SessionStore(default_timeout_minutes=15)


# AES-256-GCM Backup Encryption
def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive 256-bit key from passphrase using PBKDF2-HMAC-SHA256."""
    if HAS_CRYPTO:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(passphrase.encode('utf-8'))
    else:
        return hashlib.scrypt(passphrase.encode('utf-8'), salt=salt, n=16384, r=8, p=1, maxmem=0, dklen=32)


def encrypt_data_aes_gcm(data: bytes, passphrase: str) -> bytes:
    """
    Encrypt arbitrary bytes with AES-256-GCM.
    Returns: salt (16 bytes) + nonce (12 bytes) + ciphertext + tag
    """
    salt = secrets.token_bytes(16)
    key = derive_key(passphrase, salt)
    nonce = secrets.token_bytes(12)

    if HAS_CRYPTO:
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return salt + nonce + ciphertext
    else:
        raise RuntimeError("Cryptography library is required for AES-256-GCM encryption.")


def decrypt_data_aes_gcm(encrypted_blob: bytes, passphrase: str) -> bytes:
    """
    Decrypt AES-256-GCM encrypted backup blob.
    """
    if len(encrypted_blob) < 28:
        raise ValueError("Invalid encrypted data format or corrupted file.")

    salt = encrypted_blob[:16]
    nonce = encrypted_blob[16:28]
    ciphertext = encrypted_blob[28:]

    key = derive_key(passphrase, salt)
    if HAS_CRYPTO:
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    else:
        raise RuntimeError("Cryptography library is required for AES-256-GCM decryption.")
