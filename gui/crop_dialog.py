from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QRubberBand
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QPixmap

class CropDialog(QDialog):
    """Dialog window to manually crop the gel image before analysis."""

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop Image")
        self.setModal(True)
        self.layout = QVBoxLayout(self)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.pixmap = QPixmap(file_path)
        
        # Scale down for display if the image is too large
        self.display_pixmap = self.pixmap.scaled(
            800, 800, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(self.display_pixmap)
        self.layout.addWidget(self.image_label)
        
        self.crop_btn = QPushButton("Apply Crop")
        self.crop_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.crop_btn)
        
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.image_label)
        self.origin = QPoint()
        self.selected_rect = QRect()

        self.image_label.mousePressEvent = self.mouse_press
        self.image_label.mouseMoveEvent = self.mouse_move
        self.image_label.mouseReleaseEvent = self.mouse_release

    def mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()

    def mouse_move(self, event):
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected_rect = self.rubber_band.geometry()

    def get_crop_coordinates(self, original_shape):
        """Returns (y1, y2, x1, x2) scaled to the original numpy array shape."""
        if self.selected_rect.isNull() or self.selected_rect.width() == 0 or self.selected_rect.height() == 0:
            return None
        
        scale_x = original_shape[1] / self.display_pixmap.width()
        scale_y = original_shape[0] / self.display_pixmap.height()
        
        x1 = int(self.selected_rect.left() * scale_x)
        y1 = int(self.selected_rect.top() * scale_y)
        x2 = int(self.selected_rect.right() * scale_x)
        y2 = int(self.selected_rect.bottom() * scale_y)
        
        return y1, y2, x1, x2