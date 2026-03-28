
from __future__ import annotations

import base64
import mimetypes
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtNetwork import QHostAddress, QTcpServer, QTcpSocket

from auth import check_password, make_password_hash
from crypto import decrypt_bytes, encrypt_bytes
from database import Database
from protocol import decode_packet, encode_packet
from storage import (
    SERVER_AUDIO_DIR,
    SERVER_FILES_DIR,
    SERVER_IMAGES_DIR,
    SERVER_VIDEOS_DIR,
    ensure_server_storage,
)


class ChatServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        ensure_server_storage()
        self.host = host
        self.port = port
        self.server = QTcpServer()
        self.server.newConnection.connect(self.handle_new_connection)
        self.db = Database()
        self.buffers: Dict[QTcpSocket, str] = {}
        self.socket_user_ids: Dict[QTcpSocket, int] = {}
        self.user_sockets: Dict[int, QTcpSocket] = {}

    def start(self) -> None:
        if not self.server.listen(QHostAddress.Any, self.port):
            print(f"[SERVER] Portni ochib bo‘lmadi: {self.port}")
            sys.exit(1)
        print(f"[SERVER] Ishga tushdi: {self.host}:{self.port}")
        print("[SERVER] Ma’lumotlar saqlanish joyi AppData/Local/LANChatServer")

    def handle_new_connection(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self.buffers[socket] = ""
            socket.readyRead.connect(lambda s=socket: self.read_from_client(s))
            socket.disconnected.connect(lambda s=socket: self.handle_disconnect(s))
            print("[SERVER] Yangi client ulandi")

    def read_from_client(self, socket: QTcpSocket) -> None:
        try:
            self.buffers[socket] += socket.readAll().data().decode("utf-8")
            while "\n" in self.buffers[socket]:
                line, self.buffers[socket] = self.buffers[socket].split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                self.process_packet(socket, decode_packet(line))
        except Exception as e:
            self.send_error(socket, str(e))

    def process_packet(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        handlers = {
            "register": self.handle_register,
            "login": self.handle_login,
            "get_directory": self.handle_get_directory,
            "get_conversations": self.handle_get_conversations,
            "open_conversation": self.handle_open_conversation,
            "send_text": self.handle_send_text,
            "send_private_text": self.handle_send_private_text,
            "send_file": self.handle_send_file,
            "send_private_file": self.handle_send_private_file,
            "update_profile": self.handle_update_profile,
            "create_group": self.handle_create_group,
            "download_file": self.handle_download_file,
        }
        handler = handlers.get(packet.get("type"))
        if not handler:
            self.send_error(socket, f"Noma’lum paket turi: {packet.get('type')}")
            return
        handler(socket, packet)

    def send_packet(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        try:
            socket.write(encode_packet(packet))
            socket.flush()
        except Exception as e:
            print("[SERVER] Yuborishda xato:", e)

    def send_error(self, socket: QTcpSocket, message: str) -> None:
        self.send_packet(socket, {"type": "error", "message": message})

    def require_user_id(self, socket: QTcpSocket) -> Optional[int]:
        user_id = self.socket_user_ids.get(socket)
        if not user_id:
            self.send_error(socket, "Avval login qiling")
            return None
        return user_id

    def attach_user_to_socket(self, socket: QTcpSocket, user_id: int) -> None:
        old = self.user_sockets.get(user_id)
        if old and old is not socket:
            try:
                old.abort()
            except Exception:
                pass
            self.socket_user_ids.pop(old, None)
            self.buffers.pop(old, None)
        self.socket_user_ids[socket] = user_id
        self.user_sockets[user_id] = socket
        self.db.set_user_online(user_id, True)

    def push_directory(self, user_ids: Optional[Iterable[int]] = None) -> None:
        users = self.db.list_users()
        ids = list(user_ids) if user_ids is not None else list(self.user_sockets.keys())
        for uid in ids:
            sock = self.user_sockets.get(uid)
            if sock:
                self.send_packet(sock, {"type": "directory", "users": users})

    def push_conversations(self, user_ids: Iterable[int]) -> None:
        seen = set()
        for uid in user_ids:
            if uid in seen:
                continue
            seen.add(uid)
            sock = self.user_sockets.get(uid)
            if sock:
                self.send_packet(sock, {
                    "type": "conversations",
                    "conversations": self.db.list_conversations_for_user(uid),
                })

    def handle_register(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        username = str(packet.get("username", "")).strip()
        password = str(packet.get("password", ""))
        if not username or not password:
            self.send_error(socket, "Username va password majburiy")
            return
        if self.db.get_user_by_username(username):
            self.send_error(socket, "Bu username band")
            return
        user = self.db.create_user(
            username=username,
            password_hash=make_password_hash(password),
            full_name=packet.get("full_name"),
            email=packet.get("email"),
            phone=packet.get("phone"),
            bio=packet.get("bio"),
        )
        self.attach_user_to_socket(socket, int(user["id"]))
        self.send_packet(socket, {"type": "register_ok", "user": user})
        self.push_directory()

    def handle_login(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        username = str(packet.get("username", "")).strip()
        password = str(packet.get("password", ""))
        if not username or not password:
            self.send_error(socket, "Username va password majburiy")
            return
        row = self.db.get_user_auth_row(username)
        if not row or not check_password(password, row["password_hash"]):
            self.send_error(socket, "Login yoki password noto‘g‘ri")
            return
        user = self.db.get_user_by_id(int(row["id"]))
        assert user is not None
        self.attach_user_to_socket(socket, int(user["id"]))
        self.send_packet(socket, {"type": "login_ok", "user": user})
        self.push_directory()
        self.push_conversations([int(user["id"])])

    def handle_get_directory(self, socket: QTcpSocket, _packet: Dict[str, Any]) -> None:
        if self.require_user_id(socket) is None:
            return
        self.send_packet(socket, {"type": "directory", "users": self.db.list_users()})

    def handle_get_conversations(self, socket: QTcpSocket, _packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        self.send_packet(socket, {"type": "conversations", "conversations": self.db.list_conversations_for_user(uid)})

    def handle_open_conversation(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        try:
            conv_id = int(packet.get("conversation_id"))
        except Exception:
            self.send_error(socket, "conversation_id noto‘g‘ri")
            return
        self.db.mark_conversation_read(uid, conv_id)
        self.send_packet(socket, {"type": "messages", "conversation_id": conv_id, "messages": self.db.list_messages(conv_id)})
        self.push_conversations([uid])

    def _broadcast_message(self, conversation_id: int, message: Dict[str, Any]) -> None:
        members = self.db.get_conversation_members(conversation_id)
        ids = []
        for member in members:
            uid = int(member["id"])
            ids.append(uid)
            if uid != int(message["sender_id"]):
                self.db.mark_message_delivered(int(message["id"]), uid)
            sock = self.user_sockets.get(uid)
            if sock:
                self.send_packet(sock, {
                    "type": "message_received",
                    "conversation_id": conversation_id,
                    "message": message,
                })
        self.push_conversations(ids)

    def handle_send_text(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        text = str(packet.get("text", "")).strip()
        if not text:
            return
        try:
            conv_id = int(packet.get("conversation_id"))
        except Exception:
            self.send_error(socket, "conversation_id noto‘g‘ri")
            return
        msg = self.db.add_message(conv_id, uid, "text", body_text=text)
        self._broadcast_message(conv_id, msg)

    def handle_send_private_text(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        to_username = str(packet.get("to", "")).strip()
        text = str(packet.get("text", "")).strip()
        if not to_username or not text:
            return
        target_id = self.db.get_user_id_by_username(to_username)
        if not target_id:
            self.send_error(socket, "Foydalanuvchi topilmadi")
            return
        conv_id = self.db.get_or_create_private_conversation(uid, target_id)
        msg = self.db.add_message(conv_id, uid, "text", body_text=text)
        self._broadcast_message(conv_id, msg)

    def _store_file(self, file_name: str, raw: bytes) -> tuple[str, str, int]:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        if mime_type.startswith("image/"):
            directory = SERVER_IMAGES_DIR
            msg_type = "image"
        elif mime_type.startswith("video/"):
            directory = SERVER_VIDEOS_DIR
            msg_type = "video"
        elif mime_type.startswith("audio/"):
            directory = SERVER_AUDIO_DIR
            msg_type = "audio"
        else:
            directory = SERVER_FILES_DIR
            msg_type = "file"

        safe_name = Path(file_name).name
        target = directory / safe_name
        base = target.stem
        suffix = target.suffix
        idx = 1
        while target.exists():
            target = directory / f"{base}_{idx}{suffix}"
            idx += 1

        nonce, cipher = encrypt_bytes(raw)
        target.write_bytes(nonce + cipher)
        return str(target), msg_type, len(raw)

    def _read_file(self, file_path: str) -> bytes:
        blob = Path(file_path).read_bytes()
        nonce, cipher = blob[:12], blob[12:]
        return decrypt_bytes(nonce, cipher)

    def _send_file_common(self, uid: int, conv_id: int, file_name: str, data_b64: str) -> None:
        raw = base64.b64decode(data_b64.encode("ascii"))
        file_path, msg_type, size = self._store_file(file_name, raw)
        mime = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        msg = self.db.add_message(
            conv_id,
            uid,
            msg_type,
            file_path=file_path,
            original_name=file_name,
            file_size=size,
            mime_type=mime,
        )
        self._broadcast_message(conv_id, msg)

    def handle_send_file(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        try:
            conv_id = int(packet.get("conversation_id"))
        except Exception:
            self.send_error(socket, "conversation_id noto‘g‘ri")
            return
        file_name = str(packet.get("file_name", "")).strip()
        data_b64 = str(packet.get("data_b64", "")).strip()
        if file_name and data_b64:
            self._send_file_common(uid, conv_id, file_name, data_b64)

    def handle_send_private_file(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        to_username = str(packet.get("to", "")).strip()
        file_name = str(packet.get("file_name", "")).strip()
        data_b64 = str(packet.get("data_b64", "")).strip()
        if not to_username or not file_name or not data_b64:
            return
        target_id = self.db.get_user_id_by_username(to_username)
        if not target_id:
            self.send_error(socket, "Foydalanuvchi topilmadi")
            return
        conv_id = self.db.get_or_create_private_conversation(uid, target_id)
        self._send_file_common(uid, conv_id, file_name, data_b64)

    def handle_update_profile(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        fields = {k: packet.get(k) for k in ("full_name", "email", "phone", "bio", "avatar_path") if k in packet}
        profile = self.db.update_profile(uid, fields)
        self.send_packet(socket, {"type": "profile_updated", "profile": profile})
        self.push_directory()
        self.push_conversations([uid])

    def handle_create_group(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        uid = self.require_user_id(socket)
        if uid is None:
            return
        title = str(packet.get("title", "")).strip()
        if not title:
            self.send_error(socket, "Group nomi majburiy")
            return
        member_ids = []
        for username in packet.get("members", []):
            target_id = self.db.get_user_id_by_username(str(username))
            if target_id:
                member_ids.append(target_id)
        conv_id = self.db.create_group(title, uid, member_ids)
        self.db.add_message(conv_id, uid, "system", body_text=f"{title} group yaratildi")
        all_ids = [uid] + member_ids
        self.push_conversations(all_ids)
        self.send_packet(socket, {"type": "group_created", "conversation_id": conv_id, "title": title})

    def handle_download_file(self, socket: QTcpSocket, packet: Dict[str, Any]) -> None:
        if self.require_user_id(socket) is None:
            return
        try:
            message_id = int(packet.get("message_id"))
        except Exception:
            self.send_error(socket, "message_id noto‘g‘ri")
            return
        meta = self.db.get_message_attachment_meta(message_id)
        if not meta:
            self.send_error(socket, "Attachment topilmadi")
            return
        raw = self._read_file(meta["file_path"])
        self.send_packet(socket, {
            "type": "file_download",
            "message_id": message_id,
            "original_name": meta["original_name"],
            "mime_type": meta["mime_type"],
            "data_b64": base64.b64encode(raw).decode("ascii"),
        })

    def handle_disconnect(self, socket: QTcpSocket) -> None:
        uid = self.socket_user_ids.pop(socket, None)
        self.buffers.pop(socket, None)
        if uid:
            if self.user_sockets.get(uid) is socket:
                self.user_sockets.pop(uid, None)
            self.db.set_user_online(uid, False)
            self.push_directory()
        socket.deleteLater()


if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    server = ChatServer(port=5000)
    server.start()
    sys.exit(app.exec_())


