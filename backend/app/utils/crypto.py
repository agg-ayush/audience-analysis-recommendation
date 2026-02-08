"""Encrypt/decrypt access tokens at rest."""
import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    key = get_settings().secret_key.encode()
    # Fernet needs 32 url-safe base64-encoded bytes
    digest = hashlib.sha256(key).digest()
    b64 = base64.urlsafe_b64encode(digest)
    return Fernet(b64)


def encrypt_token(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        logger.warning("Token decryption failed (InvalidToken) — returning as-is (may be unencrypted)")
        return encrypted
