import sys
import os

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt6.QtGui import QIcon

from database.data_system import Data_system
from ui.main_window import MainWindow

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает и в dev, и в .exe)"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_style(path: str = "style.qss") -> str:
    try:
        with open(resource_path(path), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[WARNING] Файл стилей не найден: {path}")
        return ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(load_style("style.qss"))
    app.setWindowIcon(QIcon(resource_path("assets\\icon.ico")))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())