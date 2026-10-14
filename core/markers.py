import json
import os
from PyQt6.QtWidgets import (
    QDialog,QPushButton, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QLabel,QDoubleSpinBox, QSpinBox
)

class Markers:

    def __init__(self):
        self.custom_markers = {}
        
        # Determine a safe OS-specific directory for application data
        app_data_dir = os.getenv('APPDATA') # Windows
        if not app_data_dir:
            app_data_dir = os.path.expanduser('~') # macOS/Linux fallback
            
        # Create a dedicated subdirectory for your software
        self.app_dir = os.path.join(app_data_dir, "BioToolsSuite")
        os.makedirs(self.app_dir, exist_ok=True) # Ensure the folder exists
        
        self.save_file = os.path.join(self.app_dir, "custom_markers.json")

        self.default_markers = {
            "Bio-Rad - Precision Plus Dual Color": [250, 150, 100, 75, 50, 37, 25, 20, 15, 10],
            "Bio-Rad - Precision Plus Unstained": [250, 150, 100, 75, 50, 37, 25, 20, 15, 10],
            "Bio-Rad - Broad Range Unstained": [200, 116, 97, 66, 45, 31, 21, 14, 6],
            "Thermo - PageRuler Unstained": [200, 150, 120, 100, 85, 70, 50, 40, 30, 25, 20, 15, 10],
            "Thermo - PageRuler Prestained": [170, 130, 100, 70, 55, 40, 35, 25, 15, 10],
            "Thermo - PageRuler Plus Prestained": [250, 130, 100, 70, 55, 35, 25, 15, 10],
            "NEB - Color Prestained Broad Range": [245, 180, 135, 100, 75, 63, 48, 35, 25, 20, 17, 11],
            "NEB - Unstained Broad Range": [200, 150, 120, 100, 80, 60, 50, 40, 30, 25, 20, 15, 10],
            "Cytiva - Amersham ECL Rainbow": [225, 76, 52, 38, 24, 17, 12],
            "Promega - Broad Range": [225, 150, 100, 75, 50, 35, 25, 15, 10],
            "Sigma - ColorBurst": [220, 120, 100, 90, 80, 60, 50, 40, 30, 20, 15, 10]
        }
        self.load_custom()

    def load_custom(self):
        if os.path.exists(self.save_file):
            with open(self.save_file, "r") as f:
                self.custom_markers = json.load(f)

    def add_custom(self, name, bands):
        self.custom_markers[name] = bands
        with open(self.save_file, "w") as f:
            json.dump(self.custom_markers, f, indent=4)

    def get_all_markers(self) -> dict:
        all_markers = self.default_markers.copy()
        all_markers.update(self.custom_markers)
        return all_markers

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QSpinBox, QDoubleSpinBox, QLabel, QPushButton, 
    QWidget, QScrollArea
)

class CustomMarkerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Size Marker")
        self.resize(320, 420)
        
        # Main dialog layout
        main_layout = QVBoxLayout(self)

        # 1. Marker Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., My Lab Ladder")
        main_layout.addWidget(QLabel("Marker Name:"))
        main_layout.addWidget(self.name_input)

        # 2. Band Count SpinBox
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(1, 30)
        self.count_spinbox.setValue(10)
        self.count_spinbox.valueChanged.connect(self.update_band_inputs)
        
        main_layout.addWidget(QLabel("Number of bands:"))
        main_layout.addWidget(self.count_spinbox)

        # 3. Scrollable area for dynamic rows
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        self.bands_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        
        main_layout.addWidget(scroll_area)

        # List to track QDoubleSpinBox widgets
        self.band_inputs = []

        # 4. Save Button
        save_btn = QPushButton("Save Marker")
        save_btn.clicked.connect(self.accept)
        main_layout.addWidget(save_btn)

        # Initial build with default 10 bands
        self.update_band_inputs(10)

    def update_band_inputs(self, count):
        """Safely destroys old row widgets and constructs new ones."""
        # Clean up existing row widgets
        while self.bands_layout.count():
            item = self.bands_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.band_inputs.clear()

        # Build new row widgets encapsulated in a container QWidget
        for i in range(count):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)

            label = QLabel(f"Band {i+1} (kDa):")
            spinbox = QDoubleSpinBox()
            spinbox.setRange(1.0, 1000.0)
            spinbox.setDecimals(1)
            spinbox.setValue(max(10.0, 250.0 - (i * 20.0)))

            row_layout.addWidget(label)
            row_layout.addWidget(spinbox)

            self.bands_layout.addWidget(row_widget)
            self.band_inputs.append(spinbox)

    def get_marker_data(self):
        """Returns the marker name and a sorted list of unique band sizes in descending order."""
        name = self.name_input.text().strip()
        
        # Read values from spinboxes
        raw_bands = [spin.value() for spin in self.band_inputs]
        
        # Remove duplicates using set(), then sort in descending order
        bands = sorted(list(set(raw_bands)), reverse=True)
        
        return name, bands