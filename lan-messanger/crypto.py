from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from storage import SERVER_KEY_PATH, ensure_server_storage


def get_server_key() -> bytes:
    ensure_server_storage()
    if SERVER_KEY_PATH.exists():
        return SERVER_KEY_PATH.read_bytes()
    key = os.urandom(32)
    SERVER_KEY_PATH.write_bytes(key)
    return key


def encrypt_bytes(data: bytes, key: bytes | None = None) -> Tuple[bytes, bytes]:
    key = key or get_server_key()
    nonce = os.urandom(12)
    cipher = AESGCM(key).encrypt(nonce, data, None)
    return nonce, cipher


def decrypt_bytes(nonce: bytes, cipher: bytes, key: bytes | None = None) -> bytes:
    key = key or get_server_key()
    return AESGCM(key).decrypt(nonce, cipher, None)


def encrypt_text(text: str, key: bytes | None = None) -> Tuple[bytes, bytes]:
    return encrypt_bytes(text.encode("utf-8"), key)


def decrypt_text(nonce: bytes | None, cipher: bytes | None, key: bytes | None = None) -> str:
    if not nonce or not cipher:
        return ""
    return decrypt_bytes(nonce, cipher, key).decode("utf-8", errors="replace")


def hash_password(password: str, iterations: int = 200_000) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{iterations}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        iterations_s, salt_b64, digest_b64 = stored.split("$", 2)
        iterations = int(iterations_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(expected, actual)
    except Exception:
        return False
