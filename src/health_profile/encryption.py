"""
Field-level encryption for health data using Fernet (AES-128-CBC + HMAC-SHA256).
Per-user keys are derived from the master key via HKDF so a leaked user key
does not expose other users' data.
"""
import base64
import json
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

from src.config import get_settings


def _derive_user_key(user_id: str) -> bytes:
    settings = get_settings()
    master_key = base64.urlsafe_b64decode(settings.field_encryption_key)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=user_id.encode(),
        backend=default_backend(),
    )
    raw = hkdf.derive(master_key)
    return base64.urlsafe_b64encode(raw)


def encrypt_field(value: str, user_id: str) -> str:
    key = _derive_user_key(user_id)
    return Fernet(key).encrypt(value.encode()).decode()


def decrypt_field(token: str, user_id: str) -> str:
    key = _derive_user_key(user_id)
    return Fernet(key).decrypt(token.encode()).decode()


def encrypt_json(data: Any, user_id: str) -> str:
    return encrypt_field(json.dumps(data, ensure_ascii=False), user_id)


def decrypt_json(token: str, user_id: str) -> Any:
    return json.loads(decrypt_field(token, user_id))
