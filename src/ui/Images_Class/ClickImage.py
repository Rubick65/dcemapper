import numpy as np
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QLabel

class ClickImage(QLabel):

    #Signal to notify the click
    image_clicked = pyqtSignal(np.ndarray)

    def __init__(self, data, size, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedSize(size)
        #self.setMaximumSize(size)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """
        Function to emit the data if the mouse left button is pressed in the image
        :param event: Left button click
        :return: The data of the current image
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.image_clicked.emit(self.data)