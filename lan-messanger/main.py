
from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QTextOption
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from client import NetworkClient
from storage import CLIENT_DOWNLOADS_DIR, load_client_config, save_client_config


def add_shadow(widget: QWidget, blur: int = 24, x: int = 0, y: int = 6, alpha: int = 80) -> None:
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur)
    effect.setOffset(x, y)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


class ChatInputBox(QPlainTextEdit):
    sendRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.NoFrame)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.setTabChangesFocus(False)
        self.setAcceptDrops(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.document().setDocumentMargin(12)
        self.setStyleSheet(
            """
            QPlainTextEdit {
                background: transparent;
                color: #f8fbff;
                border: none;
                font-size: 15px;
                selection-background-color: #2f95ff;
                padding: 0px;
            }
            """
        )

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.sendRequested.emit()
            return
        super().keyPressEvent(event)


class ProfileDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        defaults: Optional[Dict[str, Any]] = None,
        edit_mode: bool = False,
    ):
        super().__init__(parent)
        defaults = defaults or {}
        self.edit_mode = edit_mode

        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(430, 500)
        self.setStyleSheet(
            """
            QDialog { background:#0d1727; color:#eff5fd; font-family:'Segoe UI'; }
            QLabel { color:#eaf2fc; font-size:12px; font-weight:600; }
            QLineEdit, QTextEdit {
                background:#101b2c; color:#eff5fd; border:1px solid #2a3950;
                border-radius:12px; padding:10px; font-size:13px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border:2px solid #2f95ff; background:#12213a;
            }
            QPushButton {
                background:#1f8fff; color:white; border:none; border-radius:12px;
                padding:10px 14px; font-weight:700;
            }
            QPushButton#secondary { background:#101b2c; border:1px solid #2a3950; }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.username = QLineEdit("" if not edit_mode else str(defaults.get("username") or ""))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.full_name = QLineEdit(str(defaults.get("full_name") or ""))
        self.email = QLineEdit(str(defaults.get("email") or ""))
        self.phone = QLineEdit(str(defaults.get("phone") or ""))
        self.bio = QTextEdit(str(defaults.get("bio") or ""))
        self.bio.setFixedHeight(100)

        if edit_mode:
            self.username.setReadOnly(True)
            self.password.hide()

        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username)

        if not edit_mode:
            layout.addWidget(QLabel("Password"))
            layout.addWidget(self.password)

        layout.addWidget(QLabel("Full name (optional)"))
        layout.addWidget(self.full_name)
        layout.addWidget(QLabel("Email (optional)"))
        layout.addWidget(self.email)
        layout.addWidget(QLabel("Phone (optional)"))
        layout.addWidget(self.phone)
        layout.addWidget(QLabel("Bio (optional)"))
        layout.addWidget(self.bio)

        row = QHBoxLayout()
        cancel = QPushButton("Bekor qilish")
        cancel.setObjectName("secondary")
        save = QPushButton("Saqlash")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)

    def payload(self) -> Dict[str, Any]:
        return {
            "username": self.username.text().strip(),
            "password": self.password.text(),
            "full_name": self.full_name.text().strip() or None,
            "email": self.email.text().strip() or None,
            "phone": self.phone.text().strip() or None,
            "bio": self.bio.toPlainText().strip() or None,
        }


class GroupDialog(QDialog):
    def __init__(self, parent: QWidget, users: List[Dict[str, Any]], current_username: str):
        super().__init__(parent)
        self.setWindowTitle("Yangi group")
        self.resize(400, 450)
        self.setModal(True)
        self.setStyleSheet(
            """
            QDialog { background:#0d1727; color:#eff5fd; font-family:'Segoe UI'; }
            QLabel { color:#eaf2fc; font-size:12px; font-weight:600; }
            QLineEdit, QListWidget {
                background:#101b2c; color:#eff5fd; border:1px solid #2a3950;
                border-radius:12px; padding:8px; font-size:13px;
            }
            QPushButton {
                background:#1f8fff; color:white; border:none; border-radius:12px;
                padding:10px 14px; font-weight:700;
            }
            QPushButton#secondary { background:#101b2c; border:1px solid #2a3950; }
            """
        )
        self.users = [u for u in users if u.get("username") != current_username]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Group nomi")
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for user in self.users:
            display_name = user.get("full_name") or user.get("username") or ""
            item = QListWidgetItem(display_name)
            self.list_widget.addItem(item)

        layout.addWidget(QLabel("Group nomi"))
        layout.addWidget(self.title_edit)
        layout.addWidget(QLabel("A'zolar"))
        layout.addWidget(self.list_widget)

        row = QHBoxLayout()
        cancel = QPushButton("Bekor qilish")
        cancel.setObjectName("secondary")
        ok = QPushButton("Yaratish")
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(ok)
        layout.addLayout(row)

    def data(self) -> Dict[str, Any]:
        selected_indexes = [self.list_widget.row(item) for item in self.list_widget.selectedItems()]
        members = [self.users[i]["username"] for i in selected_indexes]
        return {"title": self.title_edit.text().strip(), "members": members}


class ConversationItemWidget(QWidget):
    def __init__(self, title: str, subtitle: str, unread: int, is_stub: bool = False):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        avatar = QLabel(title[:1].upper() if title else "?")
        avatar.setFixedSize(46, 46)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "QLabel { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #2f95ff, stop:1 #7b61ff); color:white; border-radius:23px; font-weight:800; font-size:15px; }"
        )

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:14px; font-weight:800; color:#eef4fb;")
        subtitle_label = QLabel(subtitle + (" • Start chat" if is_stub else ""))
        subtitle_label.setStyleSheet("font-size:11px; color:#8ea2bd;")
        subtitle_label.setWordWrap(True)
        text_col.addWidget(title_label)
        text_col.addWidget(subtitle_label)

        layout.addWidget(avatar)
        layout.addLayout(text_col, 1)

        badge = QLabel(str(unread) if unread > 0 else "")
        badge.setFixedSize(24, 24)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            "QLabel { background:#1f8fff; color:white; border-radius:12px; font-size:11px; font-weight:800; }"
            if unread > 0 else "QLabel { background:transparent; }"
        )
        layout.addWidget(badge)


class MessageBubble(QWidget):
    downloadRequested = pyqtSignal(int)

    def __init__(self, message: Dict[str, Any], mine: bool):
        super().__init__()
        self.message = message
        self.mine = mine

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)

        bubble = QFrame()
        bubble.setMaximumWidth(620)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(18, 14, 18, 12)
        bubble_layout.setSpacing(8)

        msg_type = message.get("msg_type")
        if msg_type in ("text", "system"):
            text = message.get("body") or ""
        else:
            text = f"📎 {message.get('original_name') or msg_type or 'file'}"

        body = QLabel(text)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.setStyleSheet("font-size:14px; padding:2px;")
        bubble_layout.addWidget(body)

        if msg_type not in ("text", "system"):
            info_label = QLabel("Qabul qilish uchun tugmani bosing")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("font-size:11px; color:#d9e7ff; padding-left:2px;")
            bubble_layout.addWidget(info_label)

            btn_row = QHBoxLayout()
            btn_row.addStretch()
            download_btn = QPushButton("Yuklab olish")
            download_btn.setCursor(Qt.PointingHandCursor)
            download_btn.setFixedHeight(32)
            download_btn.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255,255,255,0.15);
                    color: white;
                    border: 1px solid rgba(255,255,255,0.18);
                    border-radius: 10px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.24);
                }
                """
            )
            download_btn.clicked.connect(self._download_clicked)
            btn_row.addWidget(download_btn)
            bubble_layout.addLayout(btn_row)

        sender_username = message.get("sender_username", "")
        created_at = str(message.get("created_at") or "")
        time_text = created_at[11:16] if len(created_at) >= 16 else created_at
        meta = QLabel(f"{sender_username}  •  {time_text}")
        meta.setStyleSheet("font-size:10px;")
        meta.setAlignment(Qt.AlignRight)
        bubble_layout.addWidget(meta)

        if mine:
            bubble.setStyleSheet(
                """
                QFrame {
                    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #2793ff, stop:1 #006dff);
                    border-radius:18px;
                }
                QLabel { color:white; background:transparent; }
                """
            )
            outer.addStretch()
            outer.addWidget(bubble)
        else:
            bubble.setStyleSheet(
                """
                QFrame {
                    background:#151f2d;
                    border:1px solid #24344b;
                    border-radius:18px;
                }
                QLabel { color:#e8eef8; background:transparent; }
                """
            )
            outer.addWidget(bubble)
            outer.addStretch()

    def _download_clicked(self) -> None:
        message_id = self.message.get("id")
        if message_id is not None:
            self.downloadRequested.emit(int(message_id))


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.client = NetworkClient()
        self.client.login_ok.connect(self._login_ok)
        self.client.register_ok.connect(self._register_ok)
        self.client.error_text.connect(self._error)
        self.chat_window: Optional[ChatWindow] = None

        cfg = load_client_config()
        self.setWindowTitle("LAN Chat")
        self.setFixedSize(620, 760)
        self.setStyleSheet(
            """
            QWidget#root { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #08111f, stop:0.5 #0d1a2f, stop:1 #091523); font-family:'Segoe UI'; }
            QFrame#card { background:rgba(16,24,38,235); border:1px solid #24334d; border-radius:28px; }
            QLabel { color:#f4f8ff; }
            QLabel#badge { background:rgba(43,140,255,35); color:#6fb4ff; border:1px solid #204a73; border-radius:12px; padding:8px 14px; font-size:11px; font-weight:700; }
            QLabel#title { font-size:36px; font-weight:800; }
            QLabel#subtitle { color:#8ea2bd; font-size:14px; }
            QLabel#field { color:#c8d5e6; font-size:12px; font-weight:700; }
            QLineEdit { background:#0f1828; color:#f3f7fd; border:1px solid #2a3950; border-radius:16px; padding-left:16px; padding-right:16px; font-size:14px; }
            QLineEdit:focus { border:2px solid #2f95ff; background:#12213a; }
            QPushButton { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2f95ff, stop:1 #006dff); color:white; border:none; border-radius:16px; font-size:15px; font-weight:800; padding:12px 16px; }
            QPushButton#secondary { background:#101b2c; border:1px solid #2a3950; }
            """
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root = QFrame()
        root.setObjectName("root")
        root_layout.addWidget(root)
        box = QVBoxLayout(root)
        box.setContentsMargins(30, 30, 30, 30)

        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, 40, 0, 12, 120)
        box.addStretch()
        box.addWidget(card)
        box.addStretch()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(38, 38, 38, 38)
        layout.setSpacing(12)

        badge = QLabel("PREMIUM LOCAL MESSENGER")
        badge.setObjectName("badge")
        title = QLabel("LAN Chat")
        title.setObjectName("title")
        sub = QLabel("Persistent baza, unread badge, group, profile va media bilan")
        sub.setObjectName("subtitle")
        sub.setWordWrap(True)

        self.server_ip = QLineEdit(str(cfg.get("server_ip", "127.0.0.1")))
        self.server_ip.setPlaceholderText("Masalan: 192.168.100.24")
        self.server_port = QLineEdit(str(cfg.get("server_port", 5000)))
        self.server_port.setPlaceholderText("5000")
        self.username = QLineEdit("")
        self.username.setPlaceholderText("Username kiriting")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password kiriting")
        self.password.setEchoMode(QLineEdit.Password)

        self.status = QLabel("")
        self.status.setStyleSheet("color:#8ea2bd; font-size:12px;")

        layout.addWidget(badge, 0, Qt.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(sub)
        for label, widget in [
            ("Server IP", self.server_ip),
            ("Port", self.server_port),
            ("Username", self.username),
            ("Password", self.password),
        ]:
            l = QLabel(label)
            l.setObjectName("field")
            widget.setFixedHeight(56)
            layout.addWidget(l)
            layout.addWidget(widget)

        row = QHBoxLayout()
        login_btn = QPushButton("Kirish")
        reg_btn = QPushButton("Ro'yxatdan o'tish")
        reg_btn.setObjectName("secondary")
        login_btn.clicked.connect(self.do_login)
        reg_btn.clicked.connect(self.do_register)
        row.addWidget(login_btn)
        row.addWidget(reg_btn)
        layout.addLayout(row)
        layout.addWidget(self.status)

    def _server(self) -> tuple[str, int]:
        host = self.server_ip.text().strip()
        port_text = self.server_port.text().strip()
        if not port_text.isdigit():
            raise ValueError("Port raqam bo‘lishi kerak")
        return host, int(port_text)

    def do_login(self) -> None:
        try:
            host, port = self._server()
        except ValueError as e:
            QMessageBox.warning(self, "Xato", str(e))
            return
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Xato", "Username va password kiriting")
            return
        save_client_config({"server_ip": host, "server_port": port})
        self.status.setText("Ulanmoqda...")
        self.client.login(host, port, username, password)

    def do_register(self) -> None:
        dialog = ProfileDialog(self, "Ro'yxatdan o'tish", defaults=None, edit_mode=False)
        if dialog.exec_() != QDialog.Accepted:
            return
        payload = dialog.payload()
        if not payload["username"] or not payload["password"]:
            QMessageBox.warning(self, "Xato", "Username va password majburiy")
            return
        try:
            host, port = self._server()
        except ValueError as e:
            QMessageBox.warning(self, "Xato", str(e))
            return
        save_client_config({"server_ip": host, "server_port": port})
        self.status.setText("Ro'yxatdan o'tmoqda...")
        self.client.register(host, port, payload)

    def _login_ok(self, payload: Dict[str, Any]) -> None:
        self.status.setText("Kirish muvaffaqiyatli")
        user = payload["user"]
        self.chat_window = ChatWindow(self.client, user, self.server_ip.text().strip(), int(self.server_port.text().strip()))
        self.chat_window.show()
        self.close()

    def _register_ok(self, payload: Dict[str, Any]) -> None:
        self._login_ok(payload)

    def _error(self, text: str) -> None:
        self.status.setText(text)


class ChatWindow(QMainWindow):
    def __init__(self, client: NetworkClient, user: Dict[str, Any], host: str, port: int):
        super().__init__()
        self.client = client
        self.me = user
        self.host = host
        self.port = port
        self.directory: List[Dict[str, Any]] = []
        self.conversations: List[Dict[str, Any]] = []
        self.sidebar_entries: List[Dict[str, Any]] = []
        self.current_conversation_id: Optional[int] = None
        self.current_peer: Optional[Dict[str, Any]] = None
        self.messages_by_conversation: Dict[int, List[Dict[str, Any]]] = {}

        self.client.directory_updated.connect(self._on_directory)
        self.client.conversations_updated.connect(self._on_conversations)
        self.client.messages_loaded.connect(self._on_messages_loaded)
        self.client.message_received.connect(self._on_message_received)
        self.client.profile_updated.connect(self._on_profile_updated)
        self.client.group_created.connect(self._on_group_created)
        self.client.file_downloaded.connect(self._on_file_downloaded)
        self.client.error_text.connect(self._on_error)
        self.client.disconnected.connect(self._on_disconnected)

        self.setWindowTitle(f"LAN Chat - {self.me['username']}")
        self.resize(1520, 920)
        self._build_ui()
        self.client.request_directory()
        self.client.request_conversations()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background:#08111f; font-family:'Segoe UI'; }
            QFrame#topbar, QFrame#leftPanel, QFrame#centerPanel, QFrame#rightPanel {
                background:#0d1727; border:1px solid #223149; border-radius:24px;
            }
            QLabel { color:#eef4fb; background:transparent; }
            QLineEdit {
                background:#101b2c; color:#eff5fd; border:1px solid #2a3950;
                border-radius:16px; padding:12px; font-size:14px;
            }
            QLineEdit:focus { border:2px solid #2f95ff; background:#12213a; }
            QListWidget { background:transparent; border:none; outline:none; }
            QListWidget::item { border-radius:16px; margin:4px 0; padding:4px; }
            QListWidget::item:selected { background:#12233a; border:1px solid #244c7a; }
            QPushButton#secondary {
                background:#101b2c; color:#dce7f6; border:1px solid #2a3950;
                border-radius:14px; font-weight:700; padding:12px 16px;
            }
            QPushButton#secondary:hover { background:#13233a; }
            QPushButton#primary {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2f95ff, stop:1 #006dff);
                color:white; border:none; border-radius:14px; font-weight:800; padding:12px 20px;
            }
            QPushButton#primary:hover { background:#2388ff; }
            """
        )

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        add_shadow(topbar)
        topbar.setFixedHeight(78)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(18, 14, 18, 14)

        badge = QLabel("LAN CHAT")
        badge.setStyleSheet(
            "QLabel { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2f95ff, stop:1 #7b61ff); color:white; border-radius:12px; padding:10px 16px; font-size:12px; font-weight:800; }"
        )
        me_info = QLabel(f"{self.me['username']}  •  Server: {self.host}:{self.port}")
        me_info.setStyleSheet("font-size:13px; color:#8ea2bd;")
        new_group = QPushButton("+ Group")
        new_group.setObjectName("secondary")
        new_group.clicked.connect(self._create_group)
        edit_profile = QPushButton("Profile")
        edit_profile.setObjectName("secondary")
        edit_profile.clicked.connect(self._edit_profile)
        tb.addWidget(badge)
        tb.addSpacing(12)
        tb.addWidget(me_info)
        tb.addStretch()
        tb.addWidget(new_group)
        tb.addWidget(edit_profile)
        root.addWidget(topbar)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # LEFT
        left = QFrame()
        left.setObjectName("leftPanel")
        add_shadow(left)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)
        left_title = QLabel("Suhbatlar")
        left_title.setStyleSheet("font-size:24px; font-weight:800;")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Qidirish...")
        self.search.textChanged.connect(self._filter_sidebar)
        self.conv_list = QListWidget()
        self.conv_list.itemClicked.connect(self._select_sidebar_entry)
        left_layout.addWidget(left_title)
        left_layout.addWidget(self.search)
        left_layout.addWidget(self.conv_list)

        # CENTER
        center = QFrame()
        center.setObjectName("centerPanel")
        add_shadow(center)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("QFrame { background:#0d1727; border-bottom:1px solid #223149; border-top-left-radius:24px; border-top-right-radius:24px; }")
        hh = QVBoxLayout(header)
        hh.setContentsMargins(22, 18, 22, 16)
        hh.setSpacing(4)
        self.chat_name = QLabel("Conversation tanlanmagan")
        self.chat_name.setStyleSheet("font-size:20px; font-weight:800;")
        self.chat_status = QLabel("Holat: —")
        self.chat_status.setStyleSheet("font-size:12px; color:#7f93af;")
        hh.addWidget(self.chat_name)
        hh.addWidget(self.chat_status)

        self.message_list = QListWidget()
        self.message_list.setStyleSheet("QListWidget { background:#091320; border:none; padding:14px; }")

        input_frame = QFrame()
        input_frame.setMinimumHeight(280)
        input_frame.setStyleSheet("QFrame { background:#0d1727; border-top:1px solid #223149; border-bottom-left-radius:24px; border-bottom-right-radius:24px; }")
        iv = QVBoxLayout(input_frame)
        iv.setContentsMargins(18, 18, 18, 18)
        iv.setSpacing(16)

        input_shell = QFrame()
        input_shell.setMinimumHeight(170)
        input_shell.setStyleSheet(
            """
            QFrame {
                background: #0f1b2d;
                border: 1px solid #2f3f59;
                border-radius: 18px;
            }
            """
        )
        input_shell_layout = QVBoxLayout(input_shell)
        input_shell_layout.setContentsMargins(12, 10, 12, 10)
        input_shell_layout.setSpacing(0)

        self.input = ChatInputBox()
        self.input.setPlaceholderText("Xabar yozing... (Enter yuboradi, Shift+Enter yangi qator)")
        self.input.setMinimumHeight(140)
        self.input.setMaximumHeight(240)
        self.input.setFont(QFont("Segoe UI", 14))
        self.input.sendRequested.connect(self._send_text)
        input_shell_layout.addWidget(self.input)

        row = QHBoxLayout()
        self.attach_btn = QPushButton("📎 Fayl")
        self.attach_btn.setObjectName("secondary")
        self.attach_btn.clicked.connect(self._send_file)
        self.media_btn = QPushButton("🖼 Media")
        self.media_btn.setObjectName("secondary")
        self.media_btn.clicked.connect(self._send_file)
        self.send_btn = QPushButton("Yuborish")
        self.send_btn.setObjectName("primary")
        self.send_btn.clicked.connect(self._send_text)
        row.addWidget(self.attach_btn)
        row.addWidget(self.media_btn)
        row.addStretch()
        row.addWidget(self.send_btn)

        iv.addWidget(input_shell)
        iv.addLayout(row)

        center_layout.addWidget(header)
        center_layout.addWidget(self.message_list, 1)
        center_layout.addWidget(input_frame)

        # RIGHT
        right = QFrame()
        right.setObjectName("rightPanel")
        add_shadow(right)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)
        right_title = QLabel("Contact Info")
        right_title.setStyleSheet("font-size:22px; font-weight:800;")
        self.avatar = QLabel((self.me["username"] or "U")[:1].upper())
        self.avatar.setFixedSize(78, 78)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet("QLabel { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #2f95ff, stop:1 #7b61ff); color:white; border-radius:39px; font-size:26px; font-weight:800; }")
        self.info_name = QLabel(self.me.get("full_name") or self.me["username"])
        self.info_name.setStyleSheet("font-size:18px; font-weight:800;")
        self.info_status = QLabel("Holat: Online")
        self.info_status.setStyleSheet("font-size:12px; color:#7f93af;")
        self.info_card = QFrame()
        self.info_card.setStyleSheet("QFrame { background:#101b2c; border:1px solid #2a3950; border-radius:18px; } QLabel { color:#dce6f4; font-size:12px; }")
        ic = QVBoxLayout(self.info_card)
        ic.setContentsMargins(16, 16, 16, 16)
        ic.setSpacing(10)
        self.info_email = QLabel()
        self.info_phone = QLabel()
        self.info_bio = QLabel()
        self.info_bio.setWordWrap(True)
        ic.addWidget(self.info_email)
        ic.addWidget(self.info_phone)
        ic.addWidget(self.info_bio)
        right_layout.addWidget(right_title)
        right_layout.addWidget(self.avatar, 0, Qt.AlignLeft)
        right_layout.addWidget(self.info_name)
        right_layout.addWidget(self.info_status)
        right_layout.addWidget(self.info_card)
        right_layout.addStretch()

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setSizes([360, 900, 320])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 8)
        splitter.setStretchFactor(2, 3)

        self.message_list.itemDoubleClicked.connect(self._message_double_clicked)
        self._set_info(self.me)

    def _set_info(self, profile: Dict[str, Any]) -> None:
        display_name = profile.get("full_name") or profile.get("title") or profile.get("username") or "—"
        self.avatar.setText((display_name or "U")[:1].upper())
        self.info_name.setText(display_name)
        self.info_status.setText("Holat: Online" if profile.get("is_online", True) else "Holat: Offline")
        self.info_email.setText(f"Email: {profile.get('email') or '—'}")
        self.info_phone.setText(f"Telefon: {profile.get('phone') or '—'}")
        self.info_bio.setText(f"Bio: {profile.get('bio') or '—'}")

    def _refresh_sidebar(self) -> None:
        current_conv = self.current_conversation_id
        current_peer = self.current_peer.get("username") if self.current_peer else None
        self.sidebar_entries.clear()
        self.conv_list.clear()

        existing_private_peers = {
            conv.get("peer_username")
            for conv in self.conversations
            if conv.get("conv_type") == "private" and conv.get("peer_username")
        }

        for conv in self.conversations:
            entry = dict(conv)
            entry["entry_type"] = "conversation"
            self.sidebar_entries.append(entry)

        for user in self.directory:
            username = user.get("username")
            if not username or username == self.me["username"]:
                continue
            if username in existing_private_peers:
                continue
            self.sidebar_entries.append({
                "entry_type": "stub",
                "conv_type": "private",
                "title": user.get("full_name") or username,
                "subtitle": user.get("bio") or "Private chat",
                "peer_username": username,
                "profile": user,
                "unread_count": 0,
            })

        for entry in self.sidebar_entries:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, entry)
            item.setSizeHint(QSize(290, 82))
            widget = ConversationItemWidget(
                entry["title"],
                entry.get("subtitle", ""),
                int(entry.get("unread_count", 0)),
                entry.get("entry_type") == "stub",
            )
            self.conv_list.addItem(item)
            self.conv_list.setItemWidget(item, widget)

        for i in range(self.conv_list.count()):
            item = self.conv_list.item(i)
            entry = item.data(Qt.UserRole)
            if current_conv is not None and entry.get("entry_type") == "conversation" and int(entry["id"]) == current_conv:
                self.conv_list.setCurrentItem(item)
                break
            if current_conv is None and current_peer and entry.get("peer_username") == current_peer:
                self.conv_list.setCurrentItem(item)
                break

        self._filter_sidebar()

    def _filter_sidebar(self) -> None:
        q = self.search.text().strip().lower()
        for i in range(self.conv_list.count()):
            item = self.conv_list.item(i)
            entry = item.data(Qt.UserRole)
            hay = f"{entry.get('title', '')} {entry.get('subtitle', '')}".lower()
            item.setHidden(q not in hay)

    def _on_directory(self, users: List[Dict[str, Any]]) -> None:
        self.directory = users
        self._refresh_sidebar()

    def _on_conversations(self, conversations: List[Dict[str, Any]]) -> None:
        self.conversations = conversations
        self._refresh_sidebar()

    def _select_sidebar_entry(self, item: QListWidgetItem) -> None:
        entry = item.data(Qt.UserRole)
        if entry.get("entry_type") == "stub":
            self.current_conversation_id = None
            self.current_peer = entry.get("profile")
            self.chat_name.setText(entry["title"])
            self.chat_status.setText("Private chat")
            self._set_info(self.current_peer or {"title": entry["title"]})
            self.message_list.clear()
            return

        conv = entry
        self.current_conversation_id = int(conv["id"])
        self.current_peer = None
        self.chat_name.setText(conv["title"])
        self.chat_status.setText("Group chat" if conv["conv_type"] == "group" else "Private chat")

        if conv["conv_type"] == "private":
            peer = next((u for u in self.directory if u.get("username") == conv.get("peer_username")), {"username": conv["title"]})
            self.current_peer = peer
            self._set_info(peer)
        else:
            self._set_info({"title": conv["title"], "bio": f"{conv.get('role', 'member')} in group"})

        self.client.open_conversation(self.current_conversation_id)

    def _on_messages_loaded(self, conversation_id: int, messages: List[Dict[str, Any]]) -> None:
        self.messages_by_conversation[conversation_id] = messages
        if self.current_conversation_id != conversation_id:
            return
        self.message_list.clear()
        for msg in messages:
            self._append_message(msg)

    def _append_message(self, msg: Dict[str, Any]) -> None:
        mine = int(msg.get("sender_id", -1)) == int(self.me["id"])
        widget = MessageBubble(msg, mine)
        widget.downloadRequested.connect(self._request_download)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.UserRole, msg)
        self.message_list.addItem(item)
        self.message_list.setItemWidget(item, widget)
        self.message_list.scrollToBottom()

    def _request_download(self, message_id: int) -> None:
        self.client.download_file(message_id)

    def _on_message_received(self, payload: Dict[str, Any]) -> None:
        conv_id = int(payload["conversation_id"])
        message = payload["message"]
        self.messages_by_conversation.setdefault(conv_id, []).append(message)
        if self.current_conversation_id == conv_id:
            self._append_message(message)
            self.client.open_conversation(conv_id)
        else:
            self.client.request_conversations()

    def _send_text(self) -> None:
        text = self.input.toPlainText().strip()
        if not text:
            return
        if self.current_conversation_id is not None:
            self.client.send_text(self.current_conversation_id, text)
            self.input.clear()
        elif self.current_peer:
            self.client.send_private_text(self.current_peer["username"], text)
            self.input.clear()
        else:
            QMessageBox.information(self, "Info", "Avval conversation tanlang")

    def _send_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Fayl tanlash")
        if not file_path:
            return
        if self.current_conversation_id is not None:
            self.client.send_file(self.current_conversation_id, file_path)
        elif self.current_peer:
            self.client.send_private_file(self.current_peer["username"], file_path)
        else:
            QMessageBox.information(self, "Info", "Avval conversation tanlang")

    def _create_group(self) -> None:
        dialog = GroupDialog(self, self.directory, self.me["username"])
        if dialog.exec_() != QDialog.Accepted:
            return
        data = dialog.data()
        if not data["title"] or not data["members"]:
            QMessageBox.warning(self, "Xato", "Group nomi va kamida 1 user tanlang")
            return
        self.client.create_group(data["title"], data["members"])

    def _edit_profile(self) -> None:
        dialog = ProfileDialog(self, "Profilni tahrirlash", defaults=self.me, edit_mode=True)
        if dialog.exec_() != QDialog.Accepted:
            return
        payload = dialog.payload()
        payload.pop("username", None)
        payload.pop("password", None)
        self.client.update_profile(payload)

    def _on_profile_updated(self, profile: Dict[str, Any]) -> None:
        self.me.update(profile)
        self._set_info(self.me)
        self.client.request_directory()

    def _on_group_created(self, payload: Dict[str, Any]) -> None:
        QMessageBox.information(self, "Group", f"Group yaratildi: {payload.get('title')}")
        self.client.request_conversations()

    def _message_double_clicked(self, item: QListWidgetItem) -> None:
        msg = item.data(Qt.UserRole) or {}
        if msg.get("msg_type") in ("text", "system"):
            return
        self.client.download_file(int(msg["id"]))

    def _on_file_downloaded(self, payload: Dict[str, Any]) -> None:
        CLIENT_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        default_name = payload.get("original_name") or "attachment.bin"
        default_path = str(CLIENT_DOWNLOADS_DIR / default_name)
        path, _ = QFileDialog.getSaveFileName(self, "Saqlash", default_path)
        if not path:
            return
        raw = base64.b64decode(payload["data_b64"].encode("ascii"))
        Path(path).write_bytes(raw)
        QMessageBox.information(self, "Saqlandi", f"Fayl saqlandi:\n{path}")

    def _on_error(self, text: str) -> None:
        QMessageBox.warning(self, "Xato", text)

    def _on_disconnected(self) -> None:
        QMessageBox.critical(self, "Ulanish uzildi", "Server bilan aloqa uzildi")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    win = AuthWindow()
    win.show()
    sys.exit(app.exec_())
