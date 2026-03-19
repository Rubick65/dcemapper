import os
import sys

import numpy as np
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QScrollArea, QLabel, \
    QSizePolicy
from nibabel.testing import data_path

from src.io.nifti_io import load_nifti, get_nifti_slices
from src.ui.Images_Class.ClickImage import ClickImage
from src.ui.Images_Class.IntensityGraph import IntensityGraph
from src.ui.Images_Class.NiftiCanvas import NiftiCanvas
from src.ui.interface.NiftiToolbar import NiftiToolbar

#-----------------CONSTANTS-----------------
window_minSize = QSize(1125, 500)

image_selector_maxSize = QSize(90, 90)

amount_image_selector_in_row = 2

main_image_minSize = QSize(400, 400)

movie_speed = 100 #miliseconds fps

name_current_dir = os.path.dirname(os.path.abspath(__file__))

class MainWindow(QMainWindow):
    def __init__(self,nifty_path = None):
        super().__init__()
        self.setWindowTitle("dcemapper")
        self.setMinimumSize(window_minSize)
        self.resize(1200, 700)
        self.nifty_path = nifty_path
        self.graphic = None
        self.canvas = None
        self.toolbar = None
        self.click_pressed = False
        self.record_layout = None
        self.data= None
        self.movie_timer = QTimer()
        self.movie_timer.timeout.connect(self.next_movie_frame)

        self.left_container = None
        self.mid_container = None
        self.right_container = None

        # Main container
        main_widget = QWidget()

        # Fill all the window
        self.setCentralWidget(main_widget)

        #Horizontal layout of widget to position other widgets
        self.main_layout = QHBoxLayout(main_widget)

        if self.nifty_path:
            #If we have data, we load it
            self.set_nifti(self.nifty_path)

        main_widget.setLayout(self.main_layout)
        self.setFocus()

    def set_nifti(self, nifty_path):
        """
        Function to load al the componets in the interface with the data
        :param nifty_path: Nifti image path
        :return: Creation of the data interface
        """
        self.nifty_path = nifty_path
        self.data, _ = load_nifti(self.nifty_path)

        #We clean the layout
        self.clear_layout(self.main_layout)

        #Create all the containers
        self.left_container = self.image_selector_layout(get_nifti_slices(self.data))
        self.mid_container = self.main_image_layout(self.data)
        self.right_container = self.graphic_layout()

        self.main_layout.addWidget(self.left_container)
        self.main_layout.addWidget(self.mid_container)
        self.main_layout.addWidget(self.right_container)

        self.update()

    def clear_layout(self, layout):
        #If layout is not empty we delete his childrens
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def clicked(self, event):
        if event.button == 1:
            self.click_pressed = True

    def no_clicked(self, event):
        if event.button == 1:
            self.click_pressed = False

    def keyPressEvent(self, event):
        """
        Events for the keypress pressed
        """
        if not self.toolbar and not event.type() == event.Type.KeyPress:
            super().keyPressEvent(event)
            return

        match event.key():
            case Qt.Key.Key_Left:
                self.toolbar.go_back()

            case Qt.Key.Key_Right:
                self.toolbar.go_forward()

            case Qt.Key.Key_Space:
                self.toggle_movie_mode()

            case Qt.Key.Key_H:
                self.toolbar.home()

            case Qt.Key.Key_Backspace:
                self.toolbar.back()

            case Qt.Key.Key_Plus:
                self.toolbar.forward()

            case Qt.Key.Key_Z:
                if not self.toolbar.mode.name == 'PAN' and not self.click_pressed:
                    self.toolbar.zoom()

            case Qt.Key.Key_M:
                if not self.toolbar.mode.name == 'ZOOM' and not self.click_pressed:
                    self.toolbar.pan()

            case Qt.Key.Key_F:
                self.toggle_fullscreen()

    def toggle_movie_mode(self):
        if self.movie_timer.isActive():
            self.movie_timer.stop()
        else:
            self.movie_timer.start(movie_speed)

    def next_movie_frame(self):
        if not self.canvas or self.data is None:
            return

        current_z = self.canvas.current_z
        total_slices = self.data.shape[2]
        next_z = (current_z + 1) % total_slices
        self.update_main_canvas_by_index(next_z)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def add_to_record(self,x,y,z,intensitis_t):
        intensity_increase = ((intensitis_t[-1] - intensitis_t[0]) / intensitis_t[0] * 100) if intensitis_t[0] != 0 else 0
        info = f"Click = {self.record_layout.count() + 1} | X = {x} | Y = {y} | Z = {z} | Intensity increase = {intensity_increase}"
        label = QLabel(info)
        #We add the info in the top of the layout
        self.record_layout.addWidget(label)

    def create_graphic(self,x,y,value):
        """
        Upload of the graphic with the pixel data
        :param x: coorX of the pixel image
        :param y: coorY of the pixel image
        :param value: Other values of the pixel image
        :return: Upload of the graphic
        """
        current_z = self.canvas.current_z
        intensities_t = self.data[x, y, current_z, :]
        self.add_to_record(x, y, current_z, intensities_t)

        #We upload the graphic with the new data
        self.graphic.update_graph(intensities_t, x, y)

    def update_main_canvas_by_index(self, index_z):
        """
        Update of the main canvas image with the Z index
        :param index_z: Current Z index of the slice that we want.
        :return: NiftiCanvas with the current Z
        """
        # If we found the old Canvas, we put the slice we want to see
        if self.canvas:
            self.canvas.set_z(index_z)
            if index_z == 0 and self.movie_timer.isActive():
                self.movie_timer.stop()

    def update_main_canvas_by_index_click(self, index_z):
        """
        Update of the main canvas image with the Z index
        And stop the movie mode if is active
        :param index_z: Current Z index of the slice that we want.
        :return: NiftiCanvas with the current Z
        """
        #If we found the old Canvas, we put the slice we want to see
        if self.canvas:
            self.canvas.set_z(index_z)
            self.movie_timer.stop() #We stop if we are in movie mode

    def normalize_img(self, img):
        """
        Function to normalize the intensity values img for display
        :param img: numpy array of data image
        :return: normalize numpy array data
        """
        #We normalize the image data to 0-255 range intensity
        if np.max(img) - np.min(img) != 0:
            norm_img = (img - np.min(img)) / (np.max(img) - np.min(img)) * 255
        else:
            #If the img has no contrast,return a black image
            norm_img = np.zeros_like(img)

        #Convert the data to unsigned 8-bit integer format for QImage compatibility
        norm_img = norm_img.astype(np.uint8)

        return norm_img

    def selector_image_creation(self, image_data, size, index):
        """
        Function to create a pixmap image
        :param image_data: path of image
        :param size: fixed size of image
        :return: Qlabel containing pixmap image
        """
        container_widget = QWidget()
        vbox = QVBoxLayout(container_widget)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        image_container = ClickImage(image_data, size)

        img = np.real(image_data)
        #We remove dimensions if we need it
        while img.ndim > 2:
            img = img[0]

        #We normalize the img data
        norm_img = self.normalize_img(img)

        height, width = norm_img.shape
        bytes_per_line = width

        q_img = QImage(norm_img.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8).copy()
        pixmap = QPixmap.fromImage(q_img)
        image_container.setPixmap(pixmap)

        #We prepare the text of each slice
        label_text = QLabel(f"Slice {index}")
        label_text.setStyleSheet("padding-top: 5px;")
        label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        vbox.addWidget(image_container)
        vbox.addWidget(label_text)

        #We add and event to each image to update the main image with this image z value
        image_container.image_clicked.connect(lambda: self.update_main_canvas_by_index_click(index))

        return container_widget

    def graphic_layout(self):
        """
        Creation of the layout that contains the graphic
        :return: the layout with the graphic created
        """
        main_container = QScrollArea()
        self.graphic = IntensityGraph()

        layout = QVBoxLayout()
        layout.addWidget(self.graphic)

        #line to separate the graphic and the record
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #444;")
        layout.addWidget(line)

        scroll = QScrollArea()
        scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scroll.setWidgetResizable(True)

        scroll_content = QWidget()
        self.record_layout = QVBoxLayout(scroll_content)
        self.record_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(scroll_content)

        layout.addWidget(QLabel("<b>Clicks record:</b>"))
        layout.addWidget(scroll)

        main_container.setMinimumWidth(350)
        #main_container.setWidgetResizable(True)
        main_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        #To prevent it from taking focus from the keyboard when it is clicked
        main_container.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        main_container.setLayout(layout)
        return main_container

    def main_image_layout(self, data):
        """
        Creation of the layout that contains the main/FigureCanvas image
        :param data: numpy array of data image
        :return: the layout with the main/FigureCanvas image inside
        """
        self.canvas = NiftiCanvas(data)
        #No focus of the keyboard when pressed
        self.canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.canvas.mpl_connect('button_press_event', self.clicked)
        self.canvas.mpl_connect('button_release_event', self.no_clicked)

        #When clicked, create the graphic
        self.canvas.set_pixel_observer(self.create_graphic)

        #Toolbar with custom options
        self.toolbar = NiftiToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setMinimumSize(main_image_minSize)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container.setLayout(layout)

        return container

    def image_selector_layout(self, images_data):
        """
        Function to create the image selector layout
        :param images_data: array of data nifti image
        :return: QScroll with all the images
        """
        container = QWidget()
        selector_layout = QVBoxLayout(container)
        selector_layout.setSpacing(30)
        selector_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Creation of rows with images with the amount indicate
        for i in range(0, len(images_data), amount_image_selector_in_row):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            #We obtein the current images range
            row_images = images_data[i:i + amount_image_selector_in_row]

            # For each image in the next 3 it will be added to the row
            for j, current_image in enumerate(row_images):
                #With the current index image in the row(0,1,2)
                #We take out the actual slice (Z)
                global_index = i + j
                image = self.selector_image_creation(current_image, image_selector_maxSize, global_index)
                row_layout.addWidget(image)
                row_layout.addSpacing(50)

            # If there are fewer images than we have indicated, we add space
            if len(row_images) < amount_image_selector_in_row:
                for _ in range(amount_image_selector_in_row - len(row_images)):
                    spacer = QWidget()
                    spacer.setFixedSize(image_selector_maxSize)
                    row_layout.addWidget(spacer, 0)
                    row_layout.addSpacing(50)

            selector_layout.addWidget(row_widget)

        selector_layout.addStretch(1)
        scroll = QScrollArea()
        scroll.setFixedWidth(280)
        scroll.setWidgetResizable(True)
        #No focus of the keyboard when clicked
        scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # deactivation of the horizontal bar
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(container)
        return scroll

if __name__ == "__main__":
    app = QApplication(sys.argv)
    example_file = os.path.join(data_path, 'example4d.nii.gz')
    window = MainWindow(example_file)
    window.show()
    sys.exit(app.exec())