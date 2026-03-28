from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

APP_NAME_SERVER = "LANChatServer"
APP_NAME_CLIENT = "LANChatClient"


def _local_appdata() -> Path:
    return Path(os.getenv("LOCALAPPDATA") or Path.home())


SERVER_BASE_DIR = _local_appdata() / APP_NAME_SERVER
SERVER_DB_DIR = SERVER_BASE_DIR / "db"
SERVER_MEDIA_DIR = SERVER_BASE_DIR / "media"
SERVER_FILES_DIR = SERVER_MEDIA_DIR / "files"
SERVER_IMAGES_DIR = SERVER_MEDIA_DIR / "images"
SERVER_VIDEOS_DIR = SERVER_MEDIA_DIR / "videos"
SERVER_AUDIO_DIR = SERVER_MEDIA_DIR / "audio"
SERVER_AVATARS_DIR = SERVER_MEDIA_DIR / "avatars"
SERVER_KEYS_DIR = SERVER_BASE_DIR / "keys"
SERVER_DB_PATH = SERVER_DB_DIR / "chat.db"
SERVER_KEY_PATH = SERVER_KEYS_DIR / "server.key"

CLIENT_BASE_DIR = _local_appdata() / APP_NAME_CLIENT
CLIENT_CACHE_DIR = CLIENT_BASE_DIR / "cache"
CLIENT_DOWNLOADS_DIR = CLIENT_BASE_DIR / "downloads"
CLIENT_CONFIG_PATH = CLIENT_BASE_DIR / "config.json"


def ensure_server_storage() -> None:
    for path in [
        SERVER_DB_DIR,
        SERVER_FILES_DIR,
        SERVER_IMAGES_DIR,
        SERVER_VIDEOS_DIR,
        SERVER_AUDIO_DIR,
        SERVER_AVATARS_DIR,
        SERVER_KEYS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def ensure_client_storage() -> None:
    for path in [CLIENT_BASE_DIR, CLIENT_CACHE_DIR, CLIENT_DOWNLOADS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_client_config() -> Dict[str, Any]:
    ensure_client_storage()
    if CLIENT_CONFIG_PATH.exists():
        try:
            return json.loads(CLIENT_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_client_config(data: Dict[str, Any]) -> None:
    ensure_client_storage()
    CLIENT_CONFIG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
