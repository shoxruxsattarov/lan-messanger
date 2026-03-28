from __future__ import annotations

from crypto import hash_password, verify_password


def make_password_hash(password: str) -> str:
    return hash_password(password)


def check_password(password: str, stored_hash: str) -> bool:
    return verify_password(password, stored_hash)
