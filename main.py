import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton

from database.data_system import Data_system
from ui.main_window import MainWindow

def load_style(path: str = "style.qss") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[WARNING] Файл стилей не найден: {path}")
        return ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(load_style("style.qss"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())