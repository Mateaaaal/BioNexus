import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QComboBox
)

from utils.density import calculate_lane_density
from core.quantification import calculate_stoichiometric_ratio


class DensitometryDialog(QDialog):
    """Dialog window displaying lane densitometry profile, peak integration, and stoichiometry."""

    def __init__(self, lane_crop: np.ndarray, lane_name: str, known_peaks: list[int], parent=None):
        super().__init__(parent)
        self.known_peaks = known_peaks
        self.setWindowTitle(f"Densitometry Profile — {lane_name}")
        self.resize(700, 620)
        self.setStyleSheet("background-color: #1E1E1E; color: #E0E0E0;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Matplotlib figure setup with professional dark theme
        self.figure = Figure(figsize=(6, 4.5), dpi=100)
        self.figure.patch.set_facecolor('#1E1E1E')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#121212')
        
        layout.addWidget(self.canvas)

        # Summary text label
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color: #A1A1A6; font-size: 11px;")
        layout.addWidget(self.summary_label)

        # Interactive Ratio UI layout
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("Stoichiometric Ratio (B1 / B2):"))
        
        combo_style = """
            QComboBox { 
                background-color: #2C2C2E; 
                color: #E0E0E0; 
                border: 1px solid #3A3A3C; 
                padding: 4px; 
                border-radius: 4px; 
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView {
                background-color: #2C2C2E;
                color: #E0E0E0;
                selection-background-color: #0A84FF;
            }
        """
        
        self.combo_b1 = QComboBox()
        self.combo_b1.setStyleSheet(combo_style)
        self.combo_b2 = QComboBox()
        self.combo_b2.setStyleSheet(combo_style)
        
        self.ratio_result_label = QLabel(" = N/A")
        self.ratio_result_label.setStyleSheet("font-weight: bold; color: #64D2FF; font-size: 13px;")

        ratio_layout.addWidget(self.combo_b1)
        ratio_layout.addWidget(QLabel("/"))
        ratio_layout.addWidget(self.combo_b2)
        ratio_layout.addWidget(self.ratio_result_label)
        ratio_layout.addStretch()
        
        layout.addLayout(ratio_layout)

        # Bottom buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3C;
                color: #FFFFFF;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #48484A;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

        # Connect dropdowns
        self.combo_b1.currentIndexChanged.connect(self.update_live_ratio)
        self.combo_b2.currentIndexChanged.connect(self.update_live_ratio)

        self.plot_profile(lane_crop)

    def plot_profile(self, lane_crop: np.ndarray):
        profile, peaks, percentages = calculate_lane_density(
            lane_crop, known_peaks=self.known_peaks
        )

        self.ax.clear()
        self.ax.set_facecolor('#121212')
        
        # Plot intensity profile with a sleek cyan accent
        self.ax.plot(
            profile, color="#64D2FF", linewidth=1.5, label="Intensity Profile"
        )

        if len(peaks) > 0:
            self.ax.plot(
                peaks, profile[peaks], "o", color="#FF3B30", markersize=6, label="Detected Bands"
            )

            summary_text = "Detected Bands Relative Abundance:\n"
            for idx, (peak, pct) in enumerate(zip(peaks, percentages)):
                self.ax.annotate(
                    f"{pct:.1f}%",
                    (peak, profile[peak]),
                    textcoords="offset points",
                    xytext=(0, 8),
                    ha="center",
                    fontsize=8,
                    weight="bold",
                    color="#E0E0E0"
                )
                summary_text += f" • Band {idx + 1}: {pct:.2f}%\n"

            self.summary_label.setText(summary_text)

            # Populate dropdowns
            self.combo_b1.clear()
            self.combo_b2.clear()
            
            for i in range(len(percentages)):
                self.combo_b1.addItem(f"Band {i+1}", percentages[i])
                self.combo_b2.addItem(f"Band {i+1}", percentages[i])

            if len(percentages) >= 2:
                self.combo_b2.setCurrentIndex(1)

        # Styling the axes to match the dark professional UI
        self.ax.set_ylabel("Relative Intensity (a.u.)", color="#8E8E93", fontsize=9)
        self.ax.set_xlabel("Migration Distance (pixels)", color="#8E8E93", fontsize=9)
        self.ax.set_title("Lane Densitometry & Integration", color="#E0E0E0", fontsize=11, fontweight='bold', pad=10)
        self.ax.tick_params(colors="#8E8E93", labelsize=8)
        self.ax.grid(True, color="#2C2C2E", linestyle=":", alpha=0.7)
        
        legend = self.ax.legend(loc="upper right", facecolor="#1E1E1E", edgecolor="#3A3A3C", labelcolor="#E0E0E0")
        for text in legend.get_texts():
            text.set_color("#E0E0E0")

        for spine in self.ax.spines.values():
            spine.set_color("#3A3A3C")
        
        self.figure.tight_layout()
        self.canvas.draw()

    def update_live_ratio(self):
        """Fetches selected band areas and updates the ratio display."""
        if self.combo_b1.count() == 0 or self.combo_b2.count() == 0:
            return
            
        area_1 = self.combo_b1.currentData()
        area_2 = self.combo_b2.currentData()
        
        ratio = calculate_stoichiometric_ratio(area_1, area_2)
        self.ratio_result_label.setText(f" = {ratio}")