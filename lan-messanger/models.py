from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PublicUser:
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    is_online: bool = False


@dataclass
class ConversationSummary:
    id: int
    conv_type: str
    title: str
    subtitle: str
    unread_count: int = 0
    peer_username: Optional[str] = None
    role: str = "member"


@dataclass
class MessageView:
    id: int
    conversation_id: int
    sender_id: int
    sender_username: str
    msg_type: str
    body: Optional[str] = None
    created_at: str = ""
    original_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
