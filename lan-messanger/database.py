from __future__ import annotations

import sqlite3
from typing import Any, Dict, Iterable, List, Optional

from crypto import decrypt_text, encrypt_text
from storage import SERVER_DB_PATH, ensure_server_storage


class Database:
    def __init__(self):
        ensure_server_storage()
        self.conn = sqlite3.connect(SERVER_DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self._create_and_migrate()

    def close(self) -> None:
        self.conn.close()

    def _table_exists(self, table_name: str) -> bool:
        self.cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table_name,),
        )
        return self.cur.fetchone() is not None

    def _columns(self, table_name: str) -> List[str]:
        if not self._table_exists(table_name):
            return []
        self.cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in self.cur.fetchall()]

    def _ensure_column(self, table_name: str, column_name: str, definition: str) -> None:
        columns = self._columns(table_name)
        if column_name not in columns:
            self.cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def _create_and_migrate(self) -> None:
        self.cur.execute("PRAGMA foreign_keys=ON")

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                bio TEXT,
                avatar_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT,
                is_online INTEGER DEFAULT 0
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_type TEXT NOT NULL,
                title TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(conversation_id, user_id),
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                msg_type TEXT NOT NULL,
                body_cipher BLOB,
                body_nonce BLOB,
                file_path TEXT,
                original_name TEXT,
                file_size INTEGER,
                mime_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS message_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                delivered_at TEXT,
                read_at TEXT,
                UNIQUE(message_id, user_id),
                FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # Migrations for older databases
        for col, definition in {
            "full_name": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "bio": "TEXT",
            "avatar_path": "TEXT",
            "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
            "last_seen": "TEXT",
            "is_online": "INTEGER DEFAULT 0",
        }.items():
            self._ensure_column("users", col, definition)

        for col, definition in {
            "title": "TEXT",
            "created_by": "INTEGER",
            "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        }.items():
            self._ensure_column("conversations", col, definition)

        for col, definition in {
            "role": "TEXT DEFAULT 'member'",
            "joined_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        }.items():
            self._ensure_column("conversation_members", col, definition)

        # Older message schemas may have body but not cipher columns.
        for col, definition in {
            "body_cipher": "BLOB",
            "body_nonce": "BLOB",
            "file_path": "TEXT",
            "original_name": "TEXT",
            "file_size": "INTEGER",
            "mime_type": "TEXT",
            "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        }.items():
            self._ensure_column("messages", col, definition)

        for col, definition in {
            "delivered_at": "TEXT",
            "read_at": "TEXT",
        }.items():
            self._ensure_column("message_status", col, definition)

        self.conn.commit()

    def _row_to_user(self, row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "username": row["username"],
            "full_name": row["full_name"],
            "email": row["email"],
            "phone": row["phone"],
            "bio": row["bio"],
            "avatar_path": row["avatar_path"],
            "is_online": bool(row["is_online"]),
        }

    def create_user(
        self,
        username: str,
        password_hash: str,
        *,
        full_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        bio: str | None = None,
    ) -> Dict[str, Any]:
        self.cur.execute(
            """
            INSERT INTO users (username, password_hash, full_name, email, phone, bio, is_online)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (username, password_hash, full_name, email, phone, bio),
        )
        self.conn.commit()
        return self.get_user_by_username(username)  # type: ignore[return-value]

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        self.cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        return self._row_to_user(self.cur.fetchone())

    def get_user_auth_row(self, username: str) -> Optional[sqlite3.Row]:
        self.cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        return self.cur.fetchone()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        self.cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return self._row_to_user(self.cur.fetchone())

    def set_user_online(self, user_id: int, online: bool) -> None:
        self.cur.execute(
            "UPDATE users SET is_online = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if online else 0, user_id),
        )
        self.conn.commit()

    def list_users(self) -> List[Dict[str, Any]]:
        self.cur.execute("SELECT * FROM users ORDER BY COALESCE(full_name, username) COLLATE NOCASE ASC")
        return [self._row_to_user(r) for r in self.cur.fetchall()]  # type: ignore[list-item]

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        self.cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = self.cur.fetchone()
        return int(row["id"]) if row else None

    def update_profile(self, user_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        allowed = ["full_name", "email", "phone", "bio", "avatar_path"]
        parts = []
        values = []
        for key in allowed:
            if key in fields:
                parts.append(f"{key} = ?")
                values.append(fields[key])
        if parts:
            values.append(user_id)
            self.cur.execute(f"UPDATE users SET {', '.join(parts)} WHERE id = ?", tuple(values))
            self.conn.commit()
        return self.get_user_by_id(user_id)  # type: ignore[return-value]

    def get_or_create_private_conversation(self, user1_id: int, user2_id: int) -> int:
        self.cur.execute(
            """
            SELECT c.id
            FROM conversations c
            JOIN conversation_members m1 ON m1.conversation_id = c.id AND m1.user_id = ?
            JOIN conversation_members m2 ON m2.conversation_id = c.id AND m2.user_id = ?
            WHERE c.conv_type = 'private'
              AND (SELECT COUNT(*) FROM conversation_members cm WHERE cm.conversation_id = c.id) = 2
            LIMIT 1
            """,
            (user1_id, user2_id),
        )
        row = self.cur.fetchone()
        if row:
            return int(row["id"])

        self.cur.execute(
            "INSERT INTO conversations (conv_type, title, created_by) VALUES ('private', NULL, ?)",
            (user1_id,),
        )
        conv_id = int(self.cur.lastrowid)
        self.cur.execute(
            "INSERT INTO conversation_members (conversation_id, user_id, role) VALUES (?, ?, 'owner')",
            (conv_id, user1_id),
        )
        self.cur.execute(
            "INSERT INTO conversation_members (conversation_id, user_id, role) VALUES (?, ?, 'member')",
            (conv_id, user2_id),
        )
        self.conn.commit()
        return conv_id

    def create_group(self, title: str, creator_id: int, member_ids: Iterable[int]) -> int:
        self.cur.execute(
            "INSERT INTO conversations (conv_type, title, created_by) VALUES ('group', ?, ?)",
            (title, creator_id),
        )
        conv_id = int(self.cur.lastrowid)
        seen = {creator_id}
        self.cur.execute(
            "INSERT INTO conversation_members (conversation_id, user_id, role) VALUES (?, ?, 'owner')",
            (conv_id, creator_id),
        )
        for user_id in member_ids:
            if user_id in seen:
                continue
            seen.add(user_id)
            self.cur.execute(
                "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, role) VALUES (?, ?, 'member')",
                (conv_id, user_id),
            )
        self.conn.commit()
        return conv_id

    def get_conversation_members(self, conversation_id: int) -> List[Dict[str, Any]]:
        self.cur.execute(
            """
            SELECT u.*, cm.role
            FROM conversation_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.conversation_id = ?
            ORDER BY COALESCE(u.full_name, u.username) COLLATE NOCASE ASC
            """,
            (conversation_id,),
        )
        out: List[Dict[str, Any]] = []
        for row in self.cur.fetchall():
            d = self._row_to_user(row)
            assert d is not None
            d["role"] = row["role"]
            out.append(d)
        return out

    def _message_row_to_view(self, row: sqlite3.Row) -> Dict[str, Any]:
        body = ""
        # New encrypted schema.
        if "body_nonce" in row.keys() and "body_cipher" in row.keys():
            body = decrypt_text(row["body_nonce"], row["body_cipher"])
        # Compatibility with very old schemas that stored plain text `body`.
        if not body and "body" in row.keys():
            body = row["body"] or ""
        return {
            "id": int(row["id"]),
            "conversation_id": int(row["conversation_id"]),
            "sender_id": int(row["sender_id"]),
            "sender_username": row["sender_username"],
            "msg_type": row["msg_type"],
            "body": body,
            "original_name": row["original_name"],
            "file_size": row["file_size"],
            "mime_type": row["mime_type"],
            "created_at": row["created_at"],
        }

    def add_message(
        self,
        conversation_id: int,
        sender_id: int,
        msg_type: str,
        *,
        body_text: str | None = None,
        file_path: str | None = None,
        original_name: str | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> Dict[str, Any]:
        nonce = None
        cipher = None
        if body_text:
            nonce, cipher = encrypt_text(body_text)

        self.cur.execute(
            """
            INSERT INTO messages (
                conversation_id, sender_id, msg_type, body_cipher, body_nonce,
                file_path, original_name, file_size, mime_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                sender_id,
                msg_type,
                cipher,
                nonce,
                file_path,
                original_name,
                file_size,
                mime_type,
            ),
        )
        message_id = int(self.cur.lastrowid)

        self.cur.execute(
            "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND user_id != ?",
            (conversation_id, sender_id),
        )
        for row in self.cur.fetchall():
            self.cur.execute(
                "INSERT INTO message_status (message_id, user_id) VALUES (?, ?)",
                (message_id, int(row["user_id"])),
            )
        self.conn.commit()
        return self.get_message(message_id)  # type: ignore[return-value]

    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        self.cur.execute(
            """
            SELECT m.*, u.username AS sender_username
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.id = ?
            """,
            (message_id,),
        )
        row = self.cur.fetchone()
        return self._message_row_to_view(row) if row else None

    def list_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        self.cur.execute(
            """
            SELECT m.*, u.username AS sender_username
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.conversation_id = ?
            ORDER BY m.id ASC
            """,
            (conversation_id,),
        )
        return [self._message_row_to_view(r) for r in self.cur.fetchall()]

    def mark_conversation_read(self, user_id: int, conversation_id: int) -> None:
        self.cur.execute(
            """
            UPDATE message_status
            SET delivered_at = COALESCE(delivered_at, CURRENT_TIMESTAMP),
                read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
            WHERE user_id = ?
              AND message_id IN (
                  SELECT id FROM messages WHERE conversation_id = ? AND sender_id != ?
              )
            """,
            (user_id, conversation_id, user_id),
        )
        self.conn.commit()

    def mark_message_delivered(self, message_id: int, user_id: int) -> None:
        self.cur.execute(
            """
            UPDATE message_status
            SET delivered_at = COALESCE(delivered_at, CURRENT_TIMESTAMP)
            WHERE message_id = ? AND user_id = ?
            """,
            (message_id, user_id),
        )
        self.conn.commit()

    def list_conversations_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        self.cur.execute(
            """
            SELECT c.*, cm.role
            FROM conversations c
            JOIN conversation_members cm ON cm.conversation_id = c.id
            WHERE cm.user_id = ?
            ORDER BY COALESCE(
                (SELECT MAX(m.created_at) FROM messages m WHERE m.conversation_id = c.id),
                c.created_at
            ) DESC, c.id DESC
            """,
            (user_id,),
        )
        out: List[Dict[str, Any]] = []
        for row in self.cur.fetchall():
            conv_id = int(row["id"])
            conv_type = row["conv_type"]
            title = row["title"] or "Conversation"
            peer_username = None
            subtitle = "No messages yet"

            self.cur.execute(
                """
                SELECT m.*, u.username AS sender_username
                FROM messages m
                JOIN users u ON u.id = m.sender_id
                WHERE m.conversation_id = ?
                ORDER BY m.id DESC
                LIMIT 1
                """,
                (conv_id,),
            )
            last_row = self.cur.fetchone()
            if last_row:
                preview = self._message_row_to_view(last_row)
                subtitle = preview["body"] if preview["msg_type"] in ("text", "system") else f"📎 {preview.get('original_name') or preview['msg_type']}"
                if not subtitle:
                    subtitle = "Text"
                if len(subtitle) > 60:
                    subtitle = subtitle[:57] + "..."

            if conv_type == "private":
                self.cur.execute(
                    """
                    SELECT u.*
                    FROM conversation_members cm
                    JOIN users u ON u.id = cm.user_id
                    WHERE cm.conversation_id = ? AND cm.user_id != ?
                    LIMIT 1
                    """,
                    (conv_id, user_id),
                )
                peer = self.cur.fetchone()
                if peer:
                    peer_username = peer["username"]
                    title = peer["full_name"] or peer["username"]

            self.cur.execute(
                """
                SELECT COUNT(*) AS unread_count
                FROM message_status ms
                JOIN messages m ON m.id = ms.message_id
                WHERE ms.user_id = ?
                  AND ms.read_at IS NULL
                  AND m.conversation_id = ?
                  AND m.sender_id != ?
                """,
                (user_id, conv_id, user_id),
            )
            unread_count = int(self.cur.fetchone()["unread_count"])

            out.append({
                "id": conv_id,
                "conv_type": conv_type,
                "title": title,
                "subtitle": subtitle,
                "peer_username": peer_username,
                "unread_count": unread_count,
                "role": row["role"],
            })
        return out

    def get_message_attachment_meta(self, message_id: int) -> Optional[Dict[str, Any]]:
        self.cur.execute(
            "SELECT id, file_path, original_name, mime_type, file_size FROM messages WHERE id = ?",
            (message_id,),
        )
        row = self.cur.fetchone()
        if not row or not row["file_path"]:
            return None
        return {
            "id": int(row["id"]),
            "file_path": row["file_path"],
            "original_name": row["original_name"],
            "mime_type": row["mime_type"],
            "file_size": row["file_size"],
        }
