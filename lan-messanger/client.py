
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QTcpSocket

from protocol import decode_packet, encode_packet


class NetworkClient(QObject):
    login_ok = pyqtSignal(dict)
    register_ok = pyqtSignal(dict)
    directory_updated = pyqtSignal(list)
    conversations_updated = pyqtSignal(list)
    messages_loaded = pyqtSignal(int, list)
    message_received = pyqtSignal(dict)
    profile_updated = pyqtSignal(dict)
    group_created = pyqtSignal(dict)
    file_downloaded = pyqtSignal(dict)
    error_text = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.socket = QTcpSocket()
        self.buffer = ""
        self.pending_packet: Optional[Dict[str, Any]] = None

        self.socket.connected.connect(self._on_connected)
        self.socket.readyRead.connect(self._on_ready_read)
        self.socket.disconnected.connect(self._on_disconnected)
        try:
            self.socket.errorOccurred.connect(self._on_error)
        except Exception:
            self.socket.error.connect(self._on_error)

    def _connect_and_send(self, host: str, port: int, packet: Dict[str, Any]) -> None:
        self.pending_packet = packet
        if self.socket.state() != QTcpSocket.UnconnectedState:
            self.socket.abort()
        self.socket.connectToHost(host, port)

    def login(self, host: str, port: int, username: str, password: str) -> None:
        self._connect_and_send(host, port, {
            "type": "login",
            "username": username,
            "password": password,
        })

    def register(self, host: str, port: int, payload: Dict[str, Any]) -> None:
        packet = {"type": "register"}
        packet.update(payload)
        self._connect_and_send(host, port, packet)

    def ensure_connected(self) -> bool:
        return self.socket.state() == QTcpSocket.ConnectedState

    def send_packet(self, packet: Dict[str, Any]) -> None:
        if not self.ensure_connected():
            self.error_text.emit("Server bilan ulanish yo‘q")
            return
        self.socket.write(encode_packet(packet))
        self.socket.flush()

    def request_directory(self) -> None:
        self.send_packet({"type": "get_directory"})

    def request_conversations(self) -> None:
        self.send_packet({"type": "get_conversations"})

    def open_conversation(self, conversation_id: int) -> None:
        self.send_packet({"type": "open_conversation", "conversation_id": conversation_id})

    def send_text(self, conversation_id: int, text: str) -> None:
        self.send_packet({"type": "send_text", "conversation_id": conversation_id, "text": text})

    def send_private_text(self, username: str, text: str) -> None:
        self.send_packet({"type": "send_private_text", "to": username, "text": text})

    def send_file(self, conversation_id: int, file_path: str) -> None:
        path = Path(file_path)
        self.send_packet({
            "type": "send_file",
            "conversation_id": conversation_id,
            "file_name": path.name,
            "data_b64": base64.b64encode(path.read_bytes()).decode("ascii"),
        })

    def send_private_file(self, username: str, file_path: str) -> None:
        path = Path(file_path)
        self.send_packet({
            "type": "send_private_file",
            "to": username,
            "file_name": path.name,
            "data_b64": base64.b64encode(path.read_bytes()).decode("ascii"),
        })

    def update_profile(self, payload: Dict[str, Any]) -> None:
        packet = {"type": "update_profile"}
        packet.update(payload)
        self.send_packet(packet)

    def create_group(self, title: str, members: list[str]) -> None:
        self.send_packet({"type": "create_group", "title": title, "members": members})

    def download_file(self, message_id: int) -> None:
        self.send_packet({"type": "download_file", "message_id": message_id})

    def _on_connected(self) -> None:
        if self.pending_packet is not None:
            packet = self.pending_packet
            self.pending_packet = None
            self.send_packet(packet)

    def _on_ready_read(self) -> None:
        try:
            self.buffer += self.socket.readAll().data().decode("utf-8")
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                self._dispatch(decode_packet(line))
        except Exception as e:
            self.error_text.emit(str(e))

    def _dispatch(self, packet: Dict[str, Any]) -> None:
        t = packet.get("type")
        if t == "login_ok":
            self.login_ok.emit(packet)
        elif t == "register_ok":
            self.register_ok.emit(packet)
        elif t == "directory":
            self.directory_updated.emit(packet.get("users", []))
        elif t == "conversations":
            self.conversations_updated.emit(packet.get("conversations", []))
        elif t == "messages":
            self.messages_loaded.emit(int(packet.get("conversation_id")), packet.get("messages", []))
        elif t == "message_received":
            self.message_received.emit(packet)
        elif t == "profile_updated":
            self.profile_updated.emit(packet.get("profile", {}))
        elif t == "group_created":
            self.group_created.emit(packet)
        elif t == "file_download":
            self.file_downloaded.emit(packet)
        elif t == "error":
            self.error_text.emit(packet.get("message", "Noma’lum xato"))
        else:
            self.error_text.emit(f"Noma’lum paket turi: {t}")

    def _on_error(self, *_args) -> None:
        self.error_text.emit(self.socket.errorString())

    def _on_disconnected(self) -> None:
        self.disconnected.emit()
