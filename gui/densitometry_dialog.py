import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from utils.density import calculate_lane_density


class DensitometryDialog(QDialog):
    def __init__(self, lane_crop: np.ndarray, lane_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Densitometry Profile - {lane_name}")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout.addWidget(self.canvas)

        self.summary_label = QLabel("")
        layout.addWidget(self.summary_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.plot_profile(lane_crop)

    def plot_profile(self, lane_crop: np.ndarray):
        profile, peaks, percentages = calculate_lane_density(lane_crop)

        self.ax.clear()
        self.ax.plot(
            profile, color="#1f77b4", linewidth=1.5, label="Intensity Profile"
        )

        if len(peaks) > 0:
            self.ax.plot(
                peaks, profile[peaks], "ro", markersize=6, label="Detected Bands"
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
                )
                summary_text += f" • Band {idx + 1}: {pct:.2f}%\n"

            self.summary_label.setText(summary_text)

        self.ax.set_ylabel("Relative Intensity (a.u.)")
        self.ax.set_xlabel("Migration Distance (pixels)")
        self.ax.set_title("Lane Densitometry & Integration")
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.ax.legend(loc="upper right")
        
        self.figure.tight_layout()
        self.canvas.draw()