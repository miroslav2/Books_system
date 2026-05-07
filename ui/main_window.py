import json
import os

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QFrame, QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtGui import QColor

from database.data_system import Data_system
from ui.books_tab import BooksWindow


SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".books_data_settings.json")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("books_data — Подключение")
        self.setMinimumSize(420, 780)
        self.setMaximumWidth(420)

        self._books_window = None
        self._build_ui()
        self._load_settings()

    # ── Построение интерфейса ─────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(30, 30, 30, 30)
        outer.setSpacing(0)

        # ── Карточка ──
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 120))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(6)

        # Заголовок
        title_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color: #e95420; font-size: 22px; background-color: #383838;")
        title = QLabel("books_data")
        title.setObjectName("sectionTitle")
        title_row.addWidget(dot)
        title_row.addWidget(title)
        title_row.addStretch()

        subtitle = QLabel("Подключение к базе данных PostgreSQL")
        subtitle.setObjectName("subtitle")

        card_layout.addLayout(title_row)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(25)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        card_layout.addWidget(div)
        card_layout.addSpacing(25)

        # Поля ввода
        self.field_dbname   = self._field(card_layout, "База данных",  "books_data")
        self.field_host     = self._field(card_layout, "Хост",         "localhost")
        self.field_user     = self._field(card_layout, "Пользователь", "postgres")
        self.field_password = self._field(card_layout, "Пароль",       "••••••••",
                                          password=True)
        card_layout.addSpacing(15)

        self.chk_remember = QCheckBox("Запомнить настройки подключения")
        card_layout.addWidget(self.chk_remember)
        card_layout.addSpacing(15)

        # Статус
        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("statusLabel")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setVisible(False)
        card_layout.addWidget(self.lbl_status)
        card_layout.addSpacing(10)

        # Кнопки
        self.btn_connect = QPushButton("Подключиться")
        self.btn_connect.setObjectName("connectBtn")
        self.btn_connect.setMinimumHeight(40)
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self._on_connect)

        btn_quit = QPushButton("Выход")
        btn_quit.setObjectName("quitBtn")
        btn_quit.setMinimumHeight(40)
        btn_quit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_quit.clicked.connect(QApplication.instance().quit)

        card_layout.addWidget(self.btn_connect)
        card_layout.addSpacing(15)
        card_layout.addWidget(btn_quit)

        outer.addStretch()
        outer.addWidget(card)
        outer.addStretch()

        ver = QLabel("v0.1.0")
        ver.setObjectName("versionLabel")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(ver)

    def _field(self, layout, label: str, placeholder: str,
               password: bool = False) -> QLineEdit:
        lbl = QLabel(label)
        lbl.setObjectName("fieldLabel")
        layout.addWidget(lbl)
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(36)
        if password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(edit)
        layout.addSpacing(10)
        return edit

    # ── Сохранение настроек ───────────────────
    def _load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            self.field_dbname.setText(data.get("dbname", ""))
            self.field_host.setText(data.get("host", ""))
            self.field_user.setText(data.get("user", ""))
            self.chk_remember.setChecked(True)
        except Exception:
            pass

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump({
                    "dbname": self.field_dbname.text(),
                    "host":   self.field_host.text(),
                    "user":   self.field_user.text(),
                }, f)
        except Exception:
            pass

    def _clear_settings(self):
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)

    # ── Логика подключения ────────────────────
    def _on_connect(self):
        dbname   = self.field_dbname.text().strip()
        host     = self.field_host.text().strip()
        user     = self.field_user.text().strip()
        password = self.field_password.text()

        if not all([dbname, host, user, password]):
            self._status("⚠  Заполните все поля", "#f57c00")
            return

        self._status("⏳  Подключение...", "#9e9e9e")
        self.btn_connect.setEnabled(False)
        QApplication.processEvents()

        try:
            db = Data_system()
            db.connect_with(host=host, dbname=dbname,
                            user=user, password=password)
        except Exception as e:
            self._status(f"✗  {e}", "#ef5350")
            self.btn_connect.setEnabled(True)
            return

        if self.chk_remember.isChecked():
            self._save_settings()
        else:
            self._clear_settings()

        self._status("✔  Успешно!", "#4caf50")
        QTimer.singleShot(500, lambda: self._open_books(db))

    def _open_books(self, db: Data_system):
        self._books_window = BooksWindow(db)
        self._books_window.show()
        self.close()

    def _status(self, text: str, color: str):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            f"QLabel#statusLabel {{ color: {color}; font-size: 12px; }}"
        )
        self.lbl_status.setVisible(True)