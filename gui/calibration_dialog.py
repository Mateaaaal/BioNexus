import numpy as np
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class CalibrationDialog(QDialog):
    """Pop-up window displaying the log10(MW) vs. migration distance linear regression curve."""
    def __init__(self, marker_sizes, marker_pixels, marker_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Calibration Curve — {marker_name}")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Matplotlib figure setup
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor('#1E1E1E')
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Plot logic
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#121212')

        log_sizes = np.log10(marker_sizes)
        slope, intercept = np.polyfit(marker_pixels, log_sizes, 1)

        # R² calculation
        p = np.poly1d([slope, intercept])
        y_pred = p(marker_pixels)
        y_bar = np.mean(log_sizes)
        ss_tot = np.sum((log_sizes - y_bar)**2)
        ss_res = np.sum((log_sizes - y_pred)**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0

        # Data points and regression line
        x_line = np.linspace(min(marker_pixels) - 10, max(marker_pixels) + 10, 100)
        y_line = slope * x_line + intercept

        ax.scatter(marker_pixels, log_sizes, color='#64D2FF', label='Marker Bands', zorder=5)
        ax.plot(x_line, y_line, color='#FF9F0A', linestyle='--', label=f'Fit: y = {slope:.4f}x + {intercept:.2f}')

        ax.set_title(f"Linear Regression (R² = {r_squared:.4f})", color='#E0E0E0', fontsize=12, fontweight='bold')
        ax.set_xlabel("Migration Distance (pixels)", color='#8E8E93')
        ax.set_ylabel("log10(MW in kDa)", color='#8E8E93')
        ax.tick_params(colors='#8E8E93')
        ax.grid(True, color='#2C2C2E', linestyle=':')
        ax.legend(facecolor='#1E1E1E', edgecolor='#3A3A3C', labelcolor='#E0E0E0')

        self.fig.tight_layout()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)