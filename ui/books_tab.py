from PyQt6.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableView,
    QHeaderView, QDialog, QFormLayout, QComboBox,
    QSpinBox, QMessageBox, QFrame, QAbstractItemView,
    QSplitter, QStatusBar, QTabWidget
)
from PyQt6.QtGui import QColor
import pandas as pd

from database.data_system import Data_system
from ui.statistic_tab import StatisticTab


# ──────────────────────────────────────────────
#  Табличная модель на основе pandas DataFrame
# ──────────────────────────────────────────────
class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame = pd.DataFrame()):
        super().__init__()
        self._df = df

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            val = self._df.iloc[index.row(), index.column()]
            return "" if pd.isna(val) else str(val)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)

    def update(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self.endResetModel()

    def get_row(self, row: int) -> pd.Series:
        return self._df.iloc[row]


# ──────────────────────────────────────────────
#  Диалог добавления / редактирования книги
# ──────────────────────────────────────────────
class BookDialog(QDialog):
    LABELS = {
        "title":     "Название *",
        "author":    "Автор *",
        "year":      "Год издания",
        "publisher": "Издательство",
        "city":      "Город",
        "style":     "Стиль",
        "pages":     "Страниц",
        "isbn":      "ISBN",
        "language":  "Язык",
    }

    # Маппинг: ключ поля формы → имя колонки в Series из get_books()
    # (колонки переименованы в COLUMN_LABELS при загрузке в таблицу)
    FIELD_TO_COL = {
        "title":     "Название",
        "author":    "Автор",
        "publisher": "Издательство",
        "city":      "Город",
        "style":     "Стиль",
        "isbn":      "ISBN",
        "language":  "Язык",
        "year":      "Год",
        "pages":     "Стр.",
    }

    def __init__(self, db: Data_system, parent=None, book: pd.Series = None):
        super().__init__(parent)
        self.db   = db
        self.book = book
        self.setWindowTitle("Редактировать книгу" if book is not None else "Добавить книгу")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._build_ui()
        if book is not None:
            self._fill_fields()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 20)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.fields = {}
        for key, label in self.LABELS.items():
            if key in ("year", "pages"):
                w = QSpinBox()
                w.setMinimumHeight(34)
                w.setRange(0, 9999)
                w.setSpecialValueText("—")
            else:
                w = QLineEdit()
                w.setMinimumHeight(34)
            self.fields[key] = w
            form.addRow(label, w)

        self.combo_shelf = QComboBox()
        self.combo_shelf.setMinimumHeight(34)
        self._shelf_ids = []
        self._populate_shelf_combo()
        form.addRow("Уровень полки *", self.combo_shelf)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_save = QPushButton("Сохранить")
        btn_save.setObjectName("connectBtn")
        btn_save.setMinimumHeight(38)
        btn_save.clicked.connect(self._on_save)

        btn_cancel = QPushButton("Отмена")
        btn_cancel.setObjectName("quitBtn")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _populate_shelf_combo(self):
        self.combo_shelf.clear()
        self._shelf_ids = []
        try:
            levels     = self.db.get_shelf_levels()
            shelves    = self.db.get_shelves()
            apartments = self.db.get_apartments()
            shelf_map  = dict(zip(shelves["id"], shelves["name"]))
            apt_map    = dict(zip(apartments["id"], apartments["name"]))
            shelf_apt  = dict(zip(shelves["id"], shelves["apartment_id"]))
            for _, row in levels.iterrows():
                shelf = shelf_map.get(row["shelf_id"], "?")
                apt   = apt_map.get(shelf_apt.get(row["shelf_id"]), "?")
                self.combo_shelf.addItem(f"{apt} → {shelf} → ур. {row['name']}")
                self._shelf_ids.append(int(row["id"]))
        except Exception as e:
            print(f"[BookDialog] combo error: {e}")

    def _fill_fields(self):
        b = self.book
        # Текстовые поля
        for field_key, col_name in self.FIELD_TO_COL.items():
            if field_key in ("year", "pages"):
                continue
            val = b.get(col_name, "")
            if pd.notna(val) and str(val).strip():
                self.fields[field_key].setText(str(val))
        # Числовые поля
        for field_key in ("year", "pages"):
            col_name = self.FIELD_TO_COL[field_key]
            val = b.get(col_name, 0)
            self.fields[field_key].setValue(int(val) if pd.notna(val) and val else 0)
        # Уровень полки
        try:
            apt   = b.get("Квартира", "")
            shelf = b.get("Шкаф", "")
            level = b.get("Уровень полки", "")
            target = f"{apt} → {shelf} → ур. {level}"
            idx = self.combo_shelf.findText(target)
            if idx >= 0:
                self.combo_shelf.setCurrentIndex(idx)
        except Exception:
            pass

    def _on_save(self):
        title  = self.fields["title"].text().strip()
        author = self.fields["author"].text().strip()
        if not title or not author:
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля: Название и Автор.")
            return

        year   = self.fields["year"].value()  or None
        pages  = self.fields["pages"].value() or None
        sl_id  = self._shelf_ids[self.combo_shelf.currentIndex()]

        def opt(k):
            v = self.fields[k].text().strip()
            return v or None

        try:
            if self.book is None:
                self.db.insert_book(title, author, year, opt("publisher"), opt("city"),
                                    opt("style"), pages, opt("isbn"), opt("language"), sl_id)
            else:
                self.db.update_book(int(self.book["ID"]), title, author, year,
                                    opt("publisher"), opt("city"), opt("style"),
                                    pages, opt("isbn"), opt("language"), sl_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))
            return
        self.accept()



# ──────────────────────────────────────────────
#  Диалог управления хранилищем
#  (Квартиры → Шкафы → Полки)
# ──────────────────────────────────────────────
class StorageDialog(QDialog):
    def __init__(self, db: Data_system, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Управление хранилищем")
        self.setMinimumSize(560, 480)
        self.setModal(True)
        self._build_ui()
        self._refresh_all()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._make_tab("apartment"), "🏠  Квартиры")
        self.tabs.addTab(self._make_tab("shelf"),     "🗄  Шкафы")
        self.tabs.addTab(self._make_tab("level"),     "📐  Полки")

        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("quitBtn")
        btn_close.setMinimumHeight(38)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    # ── Универсальная вкладка ──────────────────
    def _make_tab(self, kind: str) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Таблица
        table = QTableView()
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        model = PandasModel()
        table.setModel(model)
        layout.addWidget(table)

        # Поле ввода + родитель (для шкафов и полок)
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        name_edit = QLineEdit()
        name_edit.setMinimumHeight(34)
        input_row.addWidget(name_edit, stretch=1)

        parent_combo = QComboBox()
        parent_combo.setMinimumHeight(34)
        parent_combo.setMinimumWidth(180)

        if kind == "apartment":
            name_edit.setPlaceholderText("Название квартиры")
        elif kind == "shelf":
            name_edit.setPlaceholderText("Название шкафа")
            parent_combo.setToolTip("Квартира")
            input_row.addWidget(parent_combo)
        elif kind == "level":
            name_edit.setPlaceholderText("Номер полки (целое число)")
            parent_combo.setToolTip("Шкаф")
            input_row.addWidget(parent_combo)

        layout.addLayout(input_row)

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_add = QPushButton("＋  Добавить")
        btn_add.setObjectName("connectBtn")
        btn_add.setMinimumHeight(36)

        btn_edit = QPushButton("✎  Переименовать")
        btn_edit.setObjectName("secondaryBtn")
        btn_edit.setMinimumHeight(36)

        btn_del = QPushButton("✕  Удалить")
        btn_del.setObjectName("dangerBtn")
        btn_del.setMinimumHeight(36)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)

        # Сохраняем ссылки для обработчиков
        state = {
            "kind": kind, "table": table, "model": model,
            "name_edit": name_edit, "parent_combo": parent_combo,
        }

        btn_add.clicked.connect(lambda: self._on_add(state))
        btn_edit.clicked.connect(lambda: self._on_edit(state))
        btn_del.clicked.connect(lambda: self._on_delete(state))

        # Двойной клик → заполнить поле
        table.doubleClicked.connect(lambda idx: self._fill_from_table(state))

        setattr(self, f"_state_{kind}", state)
        return w

    # ── Заполнение из таблицы ─────────────────
    def _fill_from_table(self, state: dict):
        row = self._selected_row(state)
        if row is None:
            return
        state["name_edit"].setText(str(row.iloc[1]))  # колонка name/номер

        kind = state["kind"]
        # Выставить combo на текущего родителя
        if kind == "shelf":
            # row: (ID, Шкаф, Квартира) — ищем квартиру по имени
            apt_name = str(row.iloc[2])
            idx = state["parent_combo"].findText(apt_name)
            if idx >= 0:
                state["parent_combo"].setCurrentIndex(idx)
        elif kind == "level":
            # row: (ID, Уровень, Шкаф) — ищем шкаф по имени
            shelf_name = str(row.iloc[2])
            idx = state["parent_combo"].findText(shelf_name)
            if idx >= 0:
                state["parent_combo"].setCurrentIndex(idx)

    # ── Обновление данных ─────────────────────
    def _refresh_all(self):
        self._refresh_apartment()
        self._refresh_shelf()
        self._refresh_level()

    def _refresh_apartment(self):
        s = self._state_apartment
        df = self.db.get_apartments()
        df.columns = ["ID", "Квартира"]
        s["model"].update(df)
        s["table"].resizeColumnsToContents()

    def _refresh_shelf(self):
        s = self._state_shelf
        # Таблица с JOIN-именем квартиры
        shelves    = self.db.get_shelves()
        apartments = self.db.get_apartments()
        apt_map    = dict(zip(apartments["id"], apartments["name"]))
        shelves["apartment"] = shelves["apartment_id"].map(apt_map)
        df = shelves[["id", "name", "apartment"]].copy()
        df.columns = ["ID", "Шкаф", "Квартира"]
        s["model"].update(df)
        s["table"].resizeColumnsToContents()

        # Заполнить combo квартирами
        s["parent_combo"].blockSignals(True)
        s["parent_combo"].clear()
        self._apt_ids = []
        for _, row in apartments.iterrows():
            s["parent_combo"].addItem(row["name"])
            self._apt_ids.append(int(row["id"]))
        s["parent_combo"].blockSignals(False)

    def _refresh_level(self):
        s = self._state_level
        levels  = self.db.get_shelf_levels()
        shelves = self.db.get_shelves()
        shelf_map = dict(zip(shelves["id"], shelves["name"]))
        levels["shelf_name"] = levels["shelf_id"].map(shelf_map)
        df = levels[["id", "name", "shelf_name"]].copy()
        df.columns = ["ID", "Уровень", "Шкаф"]
        s["model"].update(df)
        s["table"].resizeColumnsToContents()

        # Заполнить combo шкафами
        s["parent_combo"].blockSignals(True)
        s["parent_combo"].clear()
        self._shelf_ids_storage = []
        for _, row in shelves.iterrows():
            s["parent_combo"].addItem(row["name"])
            self._shelf_ids_storage.append(int(row["id"]))
        s["parent_combo"].blockSignals(False)

    # ── Выбранная строка ──────────────────────
    def _selected_row(self, state: dict):
        indexes = state["table"].selectionModel().selectedRows()
        if not indexes:
            return None
        return state["model"].get_row(indexes[0].row())

    # ── CRUD ──────────────────────────────────
    def _on_add(self, state: dict):
        name = state["name_edit"].text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название.")
            return
        try:
            kind = state["kind"]
            if kind == "apartment":
                self.db.insert_apartments(name)
                self._refresh_apartment()
            elif kind == "shelf":
                if not self._apt_ids:
                    QMessageBox.warning(self, "Ошибка", "Сначала добавьте квартиру.")
                    return
                apt_id = self._apt_ids[state["parent_combo"].currentIndex()]
                self.db.insert_shelves(name, apt_id)
                self._refresh_shelf()
                self._refresh_level()   # combo шкафов в полках тоже обновится
            elif kind == "level":
                if not self._shelf_ids_storage:
                    QMessageBox.warning(self, "Ошибка", "Сначала добавьте шкаф.")
                    return
                try:
                    num = int(name)
                except ValueError:
                    QMessageBox.warning(self, "Ошибка", "Номер полки должен быть целым числом.")
                    return
                shelf_id = self._shelf_ids_storage[state["parent_combo"].currentIndex()]
                self.db.insert_shelf_levels(num, shelf_id)
                self._refresh_level()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))
            return
        state["name_edit"].clear()

    def _on_edit(self, state: dict):
        row = self._selected_row(state)
        if row is None:
            QMessageBox.information(self, "Выбор", "Выберите строку для переименования.")
            return
        name = state["name_edit"].text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите новое название.")
            return
        try:
            kind = state["kind"]
            rid  = int(row.iloc[0])
            if kind == "apartment":
                self.db.update_apartments(rid, name)
                self._refresh_apartment()
                self._refresh_shelf()
            elif kind == "shelf":
                apt_id = self._apt_ids[state["parent_combo"].currentIndex()]
                self.db.update_shelves(rid, name, apartment_id=apt_id)
                self._refresh_shelf()
                self._refresh_level()
            elif kind == "level":
                try:
                    num = int(name)
                except ValueError:
                    QMessageBox.warning(self, "Ошибка", "Номер полки должен быть целым числом.")
                    return
                shelf_id = self._shelf_ids_storage[state["parent_combo"].currentIndex()]
                self.db.update_shelf_levels(rid, num, shelf_id=shelf_id)
                self._refresh_level()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))
            return
        state["name_edit"].clear()

    def _on_delete(self, state: dict):
        row = self._selected_row(state)
        if row is None:
            QMessageBox.information(self, "Выбор", "Выберите строку для удаления.")
            return
        name_val = str(row.iloc[1])
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить «{name_val}»? Все дочерние записи тоже будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            kind = state["kind"]
            rid  = int(row.iloc[0])
            if kind == "apartment":
                self.db.delete_apartments(rid)
                self._refresh_apartment()
                self._refresh_shelf()
                self._refresh_level()
            elif kind == "shelf":
                self.db.delete_shelves(rid)
                self._refresh_shelf()
                self._refresh_level()
            elif kind == "level":
                self.db.delete_shelf_levels(rid)
                self._refresh_level()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))

# ──────────────────────────────────────────────
#  Главное окно управления БД
# ──────────────────────────────────────────────
COLUMN_LABELS = [
    "ID", "Название", "Автор", "Год", "Издательство",
    "Город", "Стиль", "Стр.", "ISBN", "Язык",
    "Уровень полки", "Шкаф", "Квартира"
]
HIDDEN_COLUMNS = {0, 8}   # id, isbn


class BooksWindow(QMainWindow):
    def __init__(self, db: Data_system):
        super().__init__()
        self.db = db
        self.setWindowTitle(f"books_data — {db.dbname}  @  {db.host}")
        self.setMinimumSize(1000, 640)
        self.resize(1200, 720)

        self._stat_visible = False
        self._build_ui()
        self._load_books()

    # ── Построение интерфейса ─────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Шапка ──
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(
            "background-color: #383838; border-bottom: 1px solid #4a4a4a;"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)
        h_layout.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet("color: #e95420; font-size: 18px;")
        title = QLabel("books_data")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        db_info = QLabel(f"{self.db.dbname}  @  {self.db.host}")
        db_info.setObjectName("subtitle")

        h_layout.addWidget(dot)
        h_layout.addWidget(title)
        h_layout.addSpacing(12)
        h_layout.addWidget(db_info)
        h_layout.addStretch()

        # Кнопка управления хранилищем
        btn_storage = QPushButton("🏠  Хранилище")
        btn_storage.setObjectName("secondaryBtn")
        btn_storage.setMinimumHeight(34)
        btn_storage.clicked.connect(self._on_storage)
        h_layout.addWidget(btn_storage)

        # Кнопка статистики
        self.btn_stat = QPushButton("📊  Статистика")
        self.btn_stat.setObjectName("secondaryBtn")
        self.btn_stat.setMinimumHeight(34)
        self.btn_stat.setCheckable(True)
        self.btn_stat.clicked.connect(self._toggle_stat)
        h_layout.addWidget(self.btn_stat)

        main_layout.addWidget(header)

        # ── Разделитель (таблица + статистика) ──
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # ── Левая часть: таблица книг ──
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 12, 16, 12)
        left_layout.setSpacing(10)

        # Тулбар
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_combo = QComboBox()
        self.search_combo.setMinimumHeight(36)
        self.search_combo.setFixedWidth(150)
        self._search_options = [
            ("Все поля",      -1),
            ("Название",       1),
            ("Автор",          2),
            ("Год",            3),
            ("Издательство",   4),
            ("Город",          5),
            ("Стиль",          6),
            ("Язык",           9),
            ("Шкаф",          11),
            ("Квартира",      12),
        ]
        for label, _ in self._search_options:
            self.search_combo.addItem(label)
        self.search_combo.currentIndexChanged.connect(self._on_search_criteria_changed)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Поиск...")
        self.search_input.setMinimumHeight(36)
        self.search_input.textChanged.connect(self._on_search)

        btn_add = QPushButton("＋  Добавить")
        btn_add.setObjectName("connectBtn")
        btn_add.setMinimumHeight(36)
        btn_add.clicked.connect(self._on_add)

        btn_edit = QPushButton("✎  Изменить")
        btn_edit.setObjectName("secondaryBtn")
        btn_edit.setMinimumHeight(36)
        btn_edit.clicked.connect(self._on_edit)

        btn_delete = QPushButton("✕  Удалить")
        btn_delete.setObjectName("dangerBtn")
        btn_delete.setMinimumHeight(36)
        btn_delete.clicked.connect(self._on_delete)

        btn_refresh = QPushButton("↺")
        btn_refresh.setObjectName("iconBtn")
        btn_refresh.setMinimumHeight(36)
        btn_refresh.setFixedWidth(40)
        btn_refresh.setToolTip("Обновить")
        btn_refresh.clicked.connect(self._load_books)

        toolbar.addWidget(self.search_combo)
        toolbar.addWidget(self.search_input, stretch=1)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        toolbar.addWidget(btn_refresh)
        left_layout.addLayout(toolbar)

        # Таблица
        self._model = PandasModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        self.table.setModel(self._proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.table.doubleClicked.connect(self._on_edit)
        left_layout.addWidget(self.table)

        # Счётчик
        self.lbl_count = QLabel()
        self.lbl_count.setObjectName("subtitle_2")
        left_layout.addWidget(self.lbl_count)

        self.splitter.addWidget(left)

        # ── Правая часть: статистика (скрыта по умолчанию) ──
        self.stat_panel = StatisticTab(self.db, parent=self)
        self.stat_panel.setVisible(False)
        self.splitter.addWidget(self.stat_panel)

        # Пропорции сплиттера: всё в таблице пока статистика скрыта
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        # ── Статусбар ──
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

    # ── Данные ──────────────────────────────
    def _load_books(self):
        df = self.db.get_books()
        df.columns = COLUMN_LABELS
        self._model.update(df)
        self.table.resizeColumnsToContents()
        for col in HIDDEN_COLUMNS:
            self.table.setColumnHidden(col, True)
        count = len(df)
        self.lbl_count.setText(f"Книг: {count}")
        self._status_bar.showMessage(
            f"  Книг в базе: {count}   |   {self.db.dbname}  @  {self.db.host}"
        )

    def _on_search_criteria_changed(self, _index: int):
        self._on_search(self.search_input.text())

    def _on_search(self, text: str):
        _, col = self._search_options[self.search_combo.currentIndex()]
        self._proxy.setFilterKeyColumn(col)
        self._proxy.setFilterFixedString(text)
        self.lbl_count.setText(f"Найдено: {self._proxy.rowCount()}")

    def _selected_book(self) -> pd.Series | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        source_row = self._proxy.mapToSource(indexes[0]).row()
        return self._model.get_row(source_row)

    # ── Хранилище ─────────────────────────
    def _on_storage(self):
        dlg = StorageDialog(self.db, parent=self)
        dlg.exec()
        # После закрытия диалога обновляем книги (полки могли измениться)
        self._load_books()

    # ── Статистика ────────────────────────
    def _toggle_stat(self, checked: bool):
        self._stat_visible = checked
        self.stat_panel.setVisible(checked)
        if checked:
            # Устанавливаем пропорцию 60/40 при первом открытии
            total = self.splitter.width()
            self.splitter.setSizes([int(total * 0.6), int(total * 0.4)])
            self.stat_panel.refresh()
            self.btn_stat.setText("✕  Закрыть статистику")
        else:
            self.splitter.setSizes([self.splitter.width(), 0])
            self.btn_stat.setText("📊  Статистика")

    # ── CRUD ────────────────────────────────
    def _on_add(self):
        dlg = BookDialog(self.db, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_books()
            if self._stat_visible:
                self.stat_panel.refresh()

    def _on_edit(self):
        book = self._selected_book()
        if book is None:
            QMessageBox.information(self, "Выбор", "Выберите книгу для редактирования.")
            return
        dlg = BookDialog(self.db, parent=self, book=book)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_books()
            if self._stat_visible:
                self.stat_panel.refresh()

    def _on_delete(self):
        book = self._selected_book()
        if book is None:
            QMessageBox.information(self, "Выбор", "Выберите книгу для удаления.")
            return
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить книгу «{book['Название']}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_book(int(book["ID"]))
            self._load_books()
            if self._stat_visible:
                self.stat_panel.refresh()