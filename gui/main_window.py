import os
import sys
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtGui import QIcon
from gui.gel_tab import GelTab

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    """ Main window of BioNexus"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("BioNexus")
        
        icon_path = get_resource_path("logo.png")
        self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1100, 750)
        
        self.load_stylesheet()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(GelTab(), "SDS-PAGE Analysis")
        
        self.setCentralWidget(self.tabs)

    def load_stylesheet(self):
        """Dark_Theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #2C2C2E;
                border: 1px solid #3A3A3C;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
                border: 1px solid #64D2FF;
                color: #64D2FF;
            }
            QLabel {
                font-size: 13px;
                margin-top: 5px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3A3A3C;
                height: 4px;
                background: #2C2C2E;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #64D2FF;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QComboBox, QSpinBox {
                background-color: #1E1E1E;
                border: 1px solid #3A3A3C;
                padding: 5px;
                border-radius: 4px;
            }
            QComboBox:hover, QSpinBox:hover {
                border: 1px solid #64D2FF;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #1E1E1E;
                border: 1px solid #3A3A3C;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #64D2FF;
                border: 1px solid #64D2FF;
            }
        """)