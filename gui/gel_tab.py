from PyQt6.QtWidgets import (
    QWidget, QCheckBox, QSlider, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QVBoxLayout, QComboBox, 
    QSpinBox, QMessageBox, QInputDialog, QGroupBox
)
from PyQt6.QtCore import Qt
import json
import base64
import io
import numpy as np
import matplotlib.pyplot as plt
import csv

from gui.canvas import GelCanvas
from core.analyzer import GelAnalyzer
from core.lane_detector import LaneDetector
from core.band_detector import BandDetector
from core.markers import Markers, CustomMarkerDialog
from gui.crop_dialog import CropDialog
from gui.calibration_dialog import CalibrationDialog


class GelTab(QWidget):
    """Main UI tab handling gel analysis workflows, parameters, and results."""

    def __init__(self):
        super().__init__()
        self._init_state()
        self._setup_ui()

    def _init_state(self):
        """Initializes internal state variables and configurations."""
        self.config = {
            "lane_prominence": 0.015,
            "lane_min_distance": 30,
            "band_prominence": 0.010,
            "band_sigma": 2.5,
            "band_distance": 15,
            "crop_dye_front": False
        }
        
        self.image_path = None
        self.raw_image_data = None
        self.display_image = None
        self.bands_per_lane = {}  
        self.annotated_bands = {}
        self.lane_names = {}

        self.marker_manager = Markers()

    def _setup_ui(self):
        """Builds the overall user interface layout."""
        main_layout = QHBoxLayout(self)
        
        # --- Left Panel (Controls) ---
        left_panel = QWidget()
        left_panel.setFixedWidth(340)  # Ensures the sidebar width is consistent
        control_layout = QVBoxLayout(left_panel)
        control_layout.setContentsMargins(0, 0, 10, 0)
        control_layout.setSpacing(15)

        # Add logic sections
        control_layout.addWidget(self._build_project_group())
        control_layout.addWidget(self._build_detection_group())
        control_layout.addWidget(self._build_calibration_group())
        
        control_layout.addStretch()  # Pushes everything up
        control_layout.addLayout(self._build_footer())

        # --- Right Panel (Canvas) ---
        self.canvas = GelCanvas()
        self.canvas.bands_modified.connect(
            lambda: self.on_marker_changed(self.marker_combo.currentData())
        )
        self.canvas.rename_requested.connect(self.rename_lane)

        # --- Main Assembly ---
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.canvas, stretch=1)
        
        self.refresh_marker_combo()

    def _build_project_group(self) -> QGroupBox:
        """Builds the Project & Data management UI section."""
        group = QGroupBox("Project & Data")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Load Image Button (Primary Action)
        self.load_btn = QPushButton("Load Gel Image")
        self.load_btn.setMinimumHeight(35)
        self.load_btn.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.load_btn.clicked.connect(self.load_image)
        layout.addWidget(self.load_btn)

        # Session Buttons
        session_layout = QHBoxLayout()
        self.load_session_btn = QPushButton("Open (.bns)")
        self.save_session_btn = QPushButton("Save (.bns)")
        self.save_session_btn.setEnabled(False)
        
        self.load_session_btn.clicked.connect(self.load_session)
        self.save_session_btn.clicked.connect(self.save_session)
        
        session_layout.addWidget(self.load_session_btn)
        session_layout.addWidget(self.save_session_btn)
        layout.addLayout(session_layout)

        # Export Buttons
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export CSV")
        self.export_img_btn = QPushButton("Export PNG")
        self.export_btn.setEnabled(False)
        self.export_img_btn.setEnabled(False)
        
        self.export_btn.clicked.connect(self.export_to_csv)
        self.export_img_btn.clicked.connect(self.export_to_png)
        
        export_layout.addWidget(self.export_btn)
        export_layout.addWidget(self.export_img_btn)
        layout.addLayout(export_layout)

        return group

    def _build_detection_group(self) -> QGroupBox:
        """Builds the Detection Parameters UI section."""
        group = QGroupBox("Detection Parameters")
        layout = QVBoxLayout(group)

        # Sensitivity Slider
        self.lane_sens_label = QLabel("Lane sensitivity:")
        layout.addWidget(self.lane_sens_label)

        self.lane_slider = QSlider(Qt.Orientation.Horizontal)
        self.lane_slider.setMinimum(1)
        self.lane_slider.setMaximum(100)
        self.lane_slider.setValue(15)
        self.lane_slider.valueChanged.connect(self.on_lane_sens_changed)
        layout.addWidget(self.lane_slider)

        # Dye Front Checkbox
        self.dye_front_check = QCheckBox("Crop dye front")
        self.dye_front_check.setChecked(False)
        self.dye_front_check.toggled.connect(self.on_dye_front_toggled)
        layout.addWidget(self.dye_front_check)

        return group

    def _build_calibration_group(self) -> QGroupBox:
        """Builds the Marker and Calibration UI section."""
        group = QGroupBox("Calibration")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Lane Selector
        lane_layout = QHBoxLayout()
        self.lane_label = QLabel("Marker Lane:")
        self.lane_spinbox = QSpinBox()
        self.lane_spinbox.setMinimum(1)
        self.lane_spinbox.valueChanged.connect(
            lambda _: self.on_marker_changed(self.marker_combo.currentData())
        )
        lane_layout.addWidget(self.lane_label)
        lane_layout.addWidget(self.lane_spinbox)
        layout.addLayout(lane_layout)

        layout.addWidget(QLabel("Select Size Marker:"))
        
        self.marker_combo = QComboBox()
        self.marker_combo.currentIndexChanged.connect(
            lambda: self.on_marker_changed(self.marker_combo.currentData())
        )
        layout.addWidget(self.marker_combo)
        
        marker_tools_layout = QHBoxLayout()
        
        self.add_marker_btn = QPushButton("+ New")
        self.add_marker_btn.setFixedWidth(60)
        self.add_marker_btn.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.add_marker_btn.clicked.connect(self.add_custom_marker)
        
        self.plot_curve_btn = QPushButton("📊 Curve")
        self.plot_curve_btn.setFixedWidth(80)
        self.plot_curve_btn.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.plot_curve_btn.setEnabled(False)
        self.plot_curve_btn.clicked.connect(self.show_calibration_curve)

        marker_tools_layout.addStretch() 
        marker_tools_layout.addWidget(self.add_marker_btn)
        marker_tools_layout.addWidget(self.plot_curve_btn)
        
        layout.addLayout(marker_tools_layout)

        # Status Label
        self.status_label = QLabel("Status: Waiting for analysis...")
        self.status_label.setStyleSheet("color: #8E8E93; font-weight: bold; font-size: 11px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        return group

    def _build_footer(self) -> QHBoxLayout:
        """Builds the footer containing help tools."""
        help_layout = QHBoxLayout()
        self.help_btn = QPushButton("ℹ️ How to Use")
        self.help_btn.setFixedSize(100, 26)
        self.help_btn.setStyleSheet("font-size: 11px; padding: 4px; background-color: #1E1E1E;")
        self.help_btn.clicked.connect(self.show_help)
        
        help_layout.addWidget(self.help_btn)
        help_layout.addStretch()
        return help_layout

    # -------------------------------------------------------------------------
    # --- Logic & Processing Methods ---
    # -------------------------------------------------------------------------

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Gel Image", "", "Images (*.png *.jpg *.jpeg *.tif *.tiff)"
        )
        if file_path:
            self.image_path = file_path
            self.raw_image_data = plt.imread(self.image_path)
            
            dialog = CropDialog(file_path, self)
            if dialog.exec():
                coords = dialog.get_crop_coordinates(self.raw_image_data.shape)
                if coords:
                    y1, y2, x1, x2 = coords
                    self.raw_image_data = self.raw_image_data[y1:y2, x1:x2]
            
            self.run_analysis()

    def run_analysis(self):
        if self.raw_image_data is None: 
            return

        gray_image = GelAnalyzer.convert_to_grayscale(self.raw_image_data)
        inverted_image = GelAnalyzer.invert_image(gray_image)
        y_start, y_end = GelAnalyzer.detect_gel_bounds(inverted_image)

        lane_detector = LaneDetector(y_start=y_start, y_end=y_end)
        lanes = lane_detector.find_lanes(
            inverted_image, 
            min_distance=self.config["lane_min_distance"],
            prominence=self.config["lane_prominence"]
        )

        band_detector = BandDetector(
            prominence=self.config["band_prominence"],
            distance=self.config["band_distance"],
            sigma=self.config["band_sigma"]
        )
        
        self.bands_per_lane.clear()
        self.lane_names.clear()

        for i, lane_x in enumerate(lanes):
            bands = band_detector.detect_bands(
                inverted_image, 
                lane_x, 
                lane_detector.lane_width, 
                y_start=y_start, 
                y_end=lane_detector.y_end,
                crop_dye_front=self.config["crop_dye_front"]
            )
            self.bands_per_lane[lane_x] = bands
            self.lane_names[lane_x] = f"L{i+1}"
        
        self.display_image = inverted_image
        self.on_marker_changed(self.marker_combo.currentData())
        
        self.export_btn.setEnabled(True)
        self.export_img_btn.setEnabled(True)
        self.save_session_btn.setEnabled(True)

    def compute_calibration_curve(self, marker_sizes, marker_pixels):
        log_sizes = np.log10(marker_sizes)
        slope, intercept = np.polyfit(marker_pixels, log_sizes, 1)
        return slope, intercept

    def calculate_protein_mass(self, band_pixel, slope, intercept):
        log_mass = slope * band_pixel + intercept
        mass = 10 ** log_mass
        return round(mass, 1)

    def on_marker_changed(self, marker_name):
        if not self.bands_per_lane or self.display_image is None or marker_name is None:
            return

        all_markers = self.marker_manager.get_all_markers()
        if marker_name not in all_markers:
            return
            
        sizes = all_markers[marker_name]

        target_lane_idx = self.lane_spinbox.value() - 1
        lanes_list = list(self.bands_per_lane.keys())
        target_lane_key = None

        if target_lane_idx < len(lanes_list):
            target_lane_key = lanes_list[target_lane_idx]
            detected_bands = self.bands_per_lane[target_lane_key]
            
            self.annotated_bands = {}
            
            if len(sizes) == len(detected_bands):
                slope, intercept = self.compute_calibration_curve(sizes, detected_bands)
                
                for lane_x, bands in self.bands_per_lane.items():
                    self.annotated_bands[lane_x] = []
                    for i, band_pixel in enumerate(bands):
                        if lane_x == target_lane_key:
                            mass = sizes[i]
                        else:
                            mass = self.calculate_protein_mass(band_pixel, slope, intercept)
                        self.annotated_bands[lane_x].append((band_pixel, mass))
                        
                self.status_label.setText("Status: Calibration OK")
                self.status_label.setStyleSheet("color: #32D74B; font-weight: bold; font-size: 11px;")
                self.plot_curve_btn.setEnabled(True)
            else:
                for lane_x, bands in self.bands_per_lane.items():
                    self.annotated_bands[lane_x] = []
                    for band_pixel in bands:
                        self.annotated_bands[lane_x].append((band_pixel, None))
                
                self.canvas.selected_lane_idx = None
                self.status_label.setText(f"Status: Mismatch! Expects {len(sizes)} bands, found {len(detected_bands)}.")
                self.status_label.setStyleSheet("color: #FF3B30; font-weight: bold; font-size: 11px;")
                self.plot_curve_btn.setEnabled(False)
        else:
            self.canvas.selected_lane_idx = None
            QMessageBox.critical(
                self, "Lane Error",
                f"Selected marker lane ({self.lane_spinbox.value()}) does not exist."
            )

        self.canvas.plot_gel(
            self.display_image, 
            lanes_list, 
            self.bands_per_lane, 
            self.annotated_bands, 
            self.lane_names, 
            target_lane_key
        )

    def on_lane_sens_changed(self, value):
        self.config["lane_prominence"] = value / 1000.0
        if self.image_path:
            self.run_analysis()

    def on_dye_front_toggled(self, checked: bool):
        self.config["crop_dye_front"] = checked
        if self.image_path:
            self.run_analysis()

    def rename_lane(self, lane_x):
        current_name = self.lane_names.get(lane_x, "")
        new_name, ok = QInputDialog.getText(
            self, "Rename Sample", 
            "Enter new name for this lane:", 
            text=current_name
        )
        if ok and new_name.strip():
            self.lane_names[lane_x] = new_name.strip()
            self.on_marker_changed(self.marker_combo.currentData())

    def refresh_marker_combo(self):
        self.marker_combo.clear()
        all_markers = self.marker_manager.get_all_markers()
        sorted_names = sorted(all_markers.keys(), key=lambda k: len(all_markers[k]), reverse=True)

        for name in sorted_names:
            band_count = len(all_markers[name])
            display_text = f"{name} ({band_count} bands)"
            self.marker_combo.addItem(display_text, name)

    def add_custom_marker(self):
        dialog = CustomMarkerDialog(self)
        if dialog.exec():
            name, bands = dialog.get_marker_data()
            if name and bands:
                self.marker_manager.add_custom(name, bands)
                self.refresh_marker_combo()
                index = self.marker_combo.findData(name)
                if index >= 0:
                    self.marker_combo.setCurrentIndex(index)
            else:
                QMessageBox.warning(self, "Invalid Input", "Please provide a valid name and band values.")

    def show_calibration_curve(self):
        marker_name = self.marker_combo.currentData()
        all_markers = self.marker_manager.get_all_markers()
        sizes = all_markers[marker_name]

        target_lane_idx = self.lane_spinbox.value() - 1
        lanes_list = list(self.bands_per_lane.keys())

        if target_lane_idx < len(lanes_list):
            target_lane_key = lanes_list[target_lane_idx]
            detected_bands = self.bands_per_lane[target_lane_key]
            dialog = CalibrationDialog(sizes, detected_bands, marker_name, self)
            dialog.exec()

    def show_help(self):
        help_text = (
            "Welcome to BioNexus - SDS-PAGE Analysis\n\n"
            "1. Load & Crop: Load your image and crop out irrelevant borders.\n\n"
            "2. Lane Adjustments: Left-click and drag the lane badges (L1, L2...) "
            "at the top of the image to adjust horizontal positions.\n\n"
            "3. Band Correction: Right-click directly on a lane to add a missing band, "
            "or right-click on an existing blue dot to remove it.\n\n"
            "4. Calibration Lock: The software will only compute molecular weights (kDa) "
            "if the selected Marker Lane has the exact number of bands expected by the catalog. "
            "Add or remove bands manually until the lock opens!"
        )
        QMessageBox.information(self, "How to Use", help_text)

    # -------------------------------------------------------------------------
    # --- File Input / Output ---
    # -------------------------------------------------------------------------

    def save_session(self):
        if self.raw_image_data is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project Session", "", "BioNexus Session (*.bns)"
        )
        if not file_path:
            return

        if not file_path.endswith('.bns'):
            file_path += '.bns'

        buffer = io.BytesIO()
        plt.imsave(buffer, self.raw_image_data, cmap='gray' if self.raw_image_data.ndim == 2 else None)
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        session_data = {
            "version": "1.0",
            "image_b64": img_b64,
            "config": self.config,
            "selected_marker": self.marker_combo.currentData(),
            "marker_lane_idx": self.lane_spinbox.value(),
            "bands_per_lane": {str(k): v for k, v in self.bands_per_lane.items()},
            "lane_names": {str(k): v for k, v in self.lane_names.items()}
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4)

        QMessageBox.information(self, "Session Saved", f"Project session saved successfully:\n{file_path}")

    def load_session(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project Session", "", "BioNexus Session (*.bns)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            img_bytes = base64.b64decode(session_data["image_b64"])
            self.raw_image_data = plt.imread(io.BytesIO(img_bytes), format='png')
            self.display_image = GelAnalyzer.invert_image(
                GelAnalyzer.convert_to_grayscale(self.raw_image_data)
            )

            self.config = session_data.get("config", self.config)
            
            self.bands_per_lane = {
                int(k) if k.isdigit() else float(k): v 
                for k, v in session_data["bands_per_lane"].items()
            }
            self.lane_names = {
                int(k) if k.isdigit() else float(k): v 
                for k, v in session_data["lane_names"].items()
            }

            saved_marker = session_data.get("selected_marker")
            if saved_marker:
                idx = self.marker_combo.findData(saved_marker)
                if idx >= 0:
                    self.marker_combo.setCurrentIndex(idx)

            self.lane_spinbox.setValue(session_data.get("marker_lane_idx", 1))

            self.export_btn.setEnabled(True)
            self.export_img_btn.setEnabled(True)
            self.save_session_btn.setEnabled(True)

            self.on_marker_changed(self.marker_combo.currentData())

        except Exception as e:
            QMessageBox.critical(self, "Error Loading Session", f"Failed to load .bns file:\n{str(e)}")

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export results", "", "CSV Files (*.csv)"
        )
        if file_path:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Lane_Name", "Band_Index", "Pixel_Position", "MW_kDa"])
                for lane_x, bands in self.annotated_bands.items():
                    for band_idx, (pixel, mass) in enumerate(bands, start=1):
                        display_mass = mass if mass is not None else "N/A"
                        writer.writerow([self.lane_names.get(lane_x), band_idx, pixel, display_mass])

            QMessageBox.information(self, "Export Successful", f"File successfully saved to:\n{file_path}")

    def export_to_png(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export image", "", "PNG Files (*.png)"
        )
        if file_path:
            self.canvas.fig.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Export Successful", f"File successfully saved to:\n{file_path}")