import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QScrollArea
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

#-----------------CONSTANTS-----------------
image_selector_maxSize = QSize(90, 90)

amount_image_selector_in_row = 3

main_image_minSize = QSize(100, 100)
main_image_maxSize = QSize(600, 600)

name_current_dir = os.path.dirname(os.path.abspath(__file__))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("dcemapper")
        self.resize(1200, 600)

        # Main container
        main_widget = QWidget()

        # Fill all the window
        self.setCentralWidget(main_widget)

        # Horizontal layout of widget to position other widgets
        main_layout = QHBoxLayout(main_widget)

        images_test = [
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
            self.get_path("C://Users//hugdp//Desktop//interface_image", "umbreon.jpg"),
        ]

        left_container = self.image_selector_layout(images_test)
        main_layout.addWidget(left_container)

        main_widget.setLayout(main_layout)

    def get_path(self, directory, image_name):
        """
        Function to get path of and image
        :param directory: Where are the image
        :param image_name: Name of the image
        :return:
        """
        return os.path.join(name_current_dir, directory, image_name)

    def image_creation(self, image, size):
        """
        Function to create a pixmap image
        :param image: path of image
        :param size: fixed size of image
        :return: Qlabel containing pixmap image
        """
        image_container = QLabel()
        pixmap = QPixmap(image)

        image_container.setPixmap(pixmap)
        image_container.setScaledContents(True)
        image_container.setFixedSize(size)
        image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return image_container

    def graphic_creation(self):
        pass

    def main_image_layout(self, image):
        pass

    def image_selector_layout(self, images):
        """
        Function to create the image selector layout
        :param images: array of images
        :return: QScroll with all the images
        """
        container = QWidget()
        selector_layout = QVBoxLayout(container)
        selector_layout.setSpacing(30)
        selector_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Creation of rows with images with the amount indicate
        for i in range(0, len(images), amount_image_selector_in_row):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_images = images[i:i + amount_image_selector_in_row]

            # For each image in the next 3 it will be added to the row
            for current_image in row_images:
                image = self.image_creation(current_image, image_selector_maxSize)
                row_layout.addWidget(image)
                row_layout.addSpacing(50)

            # If there are less of 3 images, we add space.
            if len(row_images) < amount_image_selector_in_row:
                for _ in range(amount_image_selector_in_row - len(row_images)):
                    spacer = QWidget()
                    spacer.setFixedSize(image_selector_maxSize)
                    row_layout.addWidget(spacer, 0)
                    row_layout.addSpacing(50)

            row_layout.addStretch(1)
            selector_layout.addWidget(row_widget)

        selector_layout.addStretch(1)
        scroll = QScrollArea()
        #scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        return scroll

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())