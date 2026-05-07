from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QFrame, QSizePolicy, QPushButton
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd

from database.data_system import Data_system


# ── Цвета Ubuntu Dark ─────────────────────────
ACCENT      = "#e95420"
ACCENT_FADE = "#c04010"
BG          = "#2c2c2c"
CARD_BG     = "#383838"
TEXT        = "#e0e0e0"
SUBTEXT     = "#9e9e9e"
GRID        = "#4a4a4a"
PALETTE = [
    "#e95420", "#f46b35", "#4caf50", "#2196f3",
    "#9c27b0", "#ff9800", "#00bcd4", "#8bc34a",
    "#e91e63", "#ffeb3b",
]


def _dark_axes(ax, fig):
    fig.patch.set_facecolor(CARD_BG)
    ax.set_facecolor(BG)
    ax.tick_params(colors=SUBTEXT, labelsize=10)
    ax.xaxis.label.set_color(SUBTEXT)
    ax.yaxis.label.set_color(SUBTEXT)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(color=GRID, linestyle="--", linewidth=0.5, alpha=0.6)


# ──────────────────────────────────────────────
#  Виджет одного графика
# ──────────────────────────────────────────────
class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.fig = Figure(figsize=(6, 4), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def draw_bar(self, df: pd.DataFrame, x_col: str, y_col: str,
                 title: str, limit: int = 20):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        _dark_axes(ax, self.fig)

        df = df.head(limit)
        bars = ax.barh(df[x_col].astype(str), df[y_col],
                       color=ACCENT, edgecolor="none", height=0.65)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 0.05, bar.get_y() + bar.get_height() / 2,
                    str(int(w)), va="center", ha="left",
                    color=TEXT, fontsize=9)
        ax.invert_yaxis()
        ax.set_title(title, pad=10, fontsize=13, fontweight="bold")
        ax.set_xlabel("Кол-во книг")
        self.canvas.draw()

    def draw_pie(self, df: pd.DataFrame, label_col: str, value_col: str, title: str):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor(CARD_BG)
        ax.set_facecolor(CARD_BG)

        labels = df[label_col].astype(str).tolist()
        values = df[value_col].tolist()
        colors = (PALETTE * ((len(values) // len(PALETTE)) + 1))[:len(values)]

        wedges, _, autotexts = ax.pie(
            values, colors=colors, autopct="%1.1f%%",
            startangle=140,
            wedgeprops={"edgecolor": CARD_BG, "linewidth": 1.5},
            pctdistance=0.82,
        )
        for at in autotexts:
            at.set_color(TEXT)
            at.set_fontsize(9)

        ax.legend(wedges, labels, loc="center left",
                  bbox_to_anchor=(1, 0.5), fontsize=9,
                  labelcolor=TEXT, facecolor=CARD_BG,
                  edgecolor=GRID, framealpha=0.9)
        ax.set_title(title, pad=10, fontsize=13, fontweight="bold", color=TEXT)
        self.canvas.draw()

    def draw_line(self, df: pd.DataFrame, x_col: str, y_col: str, title: str):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        _dark_axes(ax, self.fig)

        ax.plot(df[x_col].astype(str), df[y_col],
                color=ACCENT, linewidth=2, marker="o",
                markersize=5, markerfacecolor=ACCENT_FADE)
        ax.fill_between(df[x_col].astype(str), df[y_col],
                        alpha=0.15, color=ACCENT)
        ax.set_title(title, pad=10, fontsize=13, fontweight="bold")
        ax.set_xlabel("Год")
        ax.set_ylabel("Кол-во книг")

        ticks = ax.get_xticklabels()
        if len(ticks) > 15:
            step = max(1, len(ticks) // 10)
            for i, t in enumerate(ticks):
                t.set_visible(i % step == 0)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        self.canvas.draw()

    def show_empty(self, message: str = "Нет данных"):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        _dark_axes(ax, self.fig)
        ax.text(0.5, 0.5, message, ha="center", va="center",
                color=SUBTEXT, fontsize=13, transform=ax.transAxes)
        ax.set_axis_off()
        self.canvas.draw()


# ──────────────────────────────────────────────
#  Панель статистики (QWidget, встраивается в BooksWindow)
# ──────────────────────────────────────────────
class StatisticTab(QWidget):
    CHARTS = {
        "По авторам":           ("bar",  "stats_by_author",        "author",    "count"),
        "По языкам":            ("pie",  "stats_by_language",      "language",  "count"),
        "По годам":             ("line", "stats_by_year",          "year",      "count"),
        "По издательствам":     ("bar",  "stats_by_publisher",     "publisher", "count"),
        "По городам":           ("bar",  "stats_by_city",          "city",      "count"),
        "По стилям":            ("pie",  "stats_by_stile",         "stile",     "count"),
        "По стилям (%)":        ("pie",  "stats_by_stile_percent", "stile",     "percent"),
    }

    def __init__(self, db: Data_system, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Верхняя панель ──
        top = QHBoxLayout()
        top.setSpacing(10)

        lbl = QLabel("Показать:")
        lbl.setObjectName("fieldLabel")

        self.combo = QComboBox()
        self.combo.setMinimumHeight(34)
        self.combo.setMinimumWidth(220)
        for name in self.CHARTS:
            self.combo.addItem(name)
        self.combo.currentTextChanged.connect(self._render)

        self.lbl_summary = QLabel()
        self.lbl_summary.setObjectName("subtitle")

        top.addWidget(lbl)
        top.addWidget(self.combo)
        top.addSpacing(16)
        top.addWidget(self.lbl_summary)
        top.addStretch()
        layout.addLayout(top)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #4a4a4a; max-height: 1px;")
        layout.addWidget(div)

        # ── График ──
        self.chart = ChartWidget()
        layout.addWidget(self.chart)

    def refresh(self):
        """Вызвать при открытии панели или обновлении данных."""
        try:
            total   = len(self.db.get_books())
            authors = len(self.db.stats_by_author())
            langs   = len(self.db.stats_by_language())
            self.lbl_summary.setText(
                f"Всего книг: {total}   ·   Авторов: {authors}   ·   Языков: {langs}"
            )
        except Exception:
            self.lbl_summary.setText("")
        self._render(self.combo.currentText())

    def _render(self, name: str):
        if name not in self.CHARTS:
            return
        chart_type, method, label_col, value_col = self.CHARTS[name]
        try:
            df = getattr(self.db, method)()
        except Exception as e:
            self.chart.show_empty(f"Ошибка: {e}")
            return
        if df.empty:
            self.chart.show_empty("Нет данных")
            return
        if chart_type == "bar":
            self.chart.draw_bar(df, label_col, value_col, title=name)
        elif chart_type == "pie":
            self.chart.draw_pie(df, label_col, value_col, title=name)
        elif chart_type == "line":
            self.chart.draw_line(df, label_col, value_col, title=name)