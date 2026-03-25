import os
import sys
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut, QIntValidator
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QScrollArea, QLabel, \
    QSizePolicy, QSlider, QLineEdit, QSplitter
from matplotlib.widgets import RectangleSelector, EllipseSelector

from src.io.nifti_io import load_nifti, get_nifti_slices
from src.preprocessing.denoise.denoise_filter import denoise_init_one_file
from src.preprocessing.gibbs_removal.gibbs_removal import gibbs_remove
from src.roi.roi_creation import create_rectangular_mask, update_elliptical_mask_subtractive, restar_mask
from src.ui.Images_Class.ClickImage import ClickImage
from src.ui.Images_Class.IntensityGraph import IntensityGraph
from src.ui.Images_Class.NiftiCanvas import NiftiCanvas
from src.ui.file_explorer.file_explorer import TopMenu
from src.ui.interface.NiftiToolbar import NiftiToolbar
from src.utils.utils import create_output_folder

# -----------------CONSTANTS-----------------
window_minSize = QSize(1125, 500)

image_in_selector_maxSize = QSize(90, 90)
selector_minWidth = 280

amount_image_selector_in_row = 2

main_image_minSize = QSize(400, 400)

name_current_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QMainWindow):
    def __init__(self, nifty_path=None):
        super().__init__()
        self.mask_history = []
        self.file_list = None
        self.current_mask_counter = -1
        self.setWindowTitle("dcemapper")
        self.setMinimumSize(window_minSize)
        self.screen_size = self.screen().availableGeometry()  # Window size
        width = int(self.screen_size.width() * 0.4)
        height = int(self.screen_size.height() * 0.7)
        self.resize(width, height)
        self.nifty_path = nifty_path
        self.movie_speed = 30  # miliseconds fps
        self._shortcuts = []
        self.graphic = None
        self.canvas = None
        self.toolbar = None
        self.slider_t = None
        self.slider_t_input = None
        self.slider_fps = None
        self.slider_fps_input = None
        self.input_x = None
        self.input_y = None
        self.x = None
        self.y = None
        self.selector_layout = None
        self.click_pressed = False
        self.record_layout = None
        self.data = None
        self.full_mask = None
        self.original_data = None
        self.current_subject = None
        self.derivative_folder = None
        self.movie_timer = QTimer()
        self.movie_timer.timeout.connect(self.next_movie_frame)

        self.left_container = None
        self.mid_container = None
        self.right_container = None

        self.main_splitter = None

        self.current_roi = None
        self.roi_selector_list = []
        self.selected_roi = ""
        self.top_bar = TopMenu()
        self.top_bar.deactivate()
        self.setMenuBar(self.top_bar)
        self.top_bar.file_menu.files_signal.connect(self.set_various_files)
        self.top_bar.file_menu.one_file_signal.connect(self.set_various_files)
        self.top_bar.preprocessing_menu.preprocess_signal.connect(self.preprocessing)

        # Main container
        main_widget = QWidget()

        # Fill all the window
        self.setCentralWidget(main_widget)

        # Horizontal layout of widget to position the splitter
        self.main_layout = QHBoxLayout(main_widget)

        if self.nifty_path:
            # If we have data, we load it
            self.set_nifti(self.nifty_path)
            self.setFocus()
            self.init_shortcuts()

        main_widget.setLayout(self.main_layout)

    def preprocessing(self, selected_preprocess_options):
        denoise_filter, gibbs = selected_preprocess_options

        output_folder = create_output_folder(self.current_subject if self.current_subject else "Unknown",
                                             self.derivative_folder)
        data = self.nifty_path

        if denoise_filter:
            data = denoise_init_one_file(self.nifty_path, output_folder, denoise_filter)

        if gibbs:
            data = gibbs_remove([data])

        self.nifty_path = data

        self.data, _ = load_nifti(data)
        self.original_data = self.data 
        self.toolbar.roi_menu.activate_roi_selection()

        roi_slices = get_nifti_slices(self.data)
        self.update_widgets(roi_slices)

    def set_one_file(self, nifty_path):
        if nifty_path:
            path_obj = Path(nifty_path)

            self.current_subject = path_obj.parent.parent.name
            self.set_nifti(nifty_path)

    def set_various_files(self, nifty_data):
        nifty_path, derivative_folder = nifty_data
        if isinstance(nifty_path, tuple):
            self.current_subject = nifty_path[0]  # Name of the subject
            nifty_path = nifty_path[1]

        self.derivative_folder = derivative_folder

        self.set_nifti(nifty_path)

    def set_nifti(self, nifty_path):
        """
        Function to load al the componets in the interface with the data
        :param nifty_path: Nifti image path
        :return: Creation of the data interface
        """
        if nifty_path == "":
            return

        self.movie_timer.stop()
        self.movie_speed = 30

        if self.canvas:
            self.canvas.current_z = 0
            self.canvas.current_t = 0
            self.canvas.subject_text = None
            self.canvas.close_figure()
            self.canvas.deleteLater()
            self.canvas = None

        if self.slider_t:
            self.slider_t.setValue(0)

        if self.graphic:
            self.graphic.close_graph()
            self.graphic.deleteLater()
            self.graphic = None

        max_x, max_y = self.get_max_coordinates()
        if self.x and self.y:
            self.x.validator().setTop(max_x)
            self.y.validator().setTop(max_y)
            self.x.setText("0")
            self.y.setText("0")

        self.mask_history = []
        self.current_mask_counter = -1
        self.current_roi = None

        self.nifty_path = nifty_path
        self.data, _ = load_nifti(self.nifty_path)
        self.original_data = self.data.copy()
        self.full_mask = np.ones(self.data.shape[:3], dtype=bool)

        # We clean the layout
        self.clear_layout(self.main_layout)

        # Splitter to drag the mid and right containers sizes
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create all the containers
        self.left_container = self.image_selector_layout(get_nifti_slices(self.data))
        self.mid_container = self.main_image_layout(self.data, self.current_subject)
        self.right_container = self.graphic_layout()

        self.main_layout.addWidget(self.left_container)
        self.main_splitter.addWidget(self.mid_container)
        self.main_splitter.addWidget(self.right_container)

        # To prevent that the containers collapse each to other
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)

        total_w = self.width()
        # Sizes of splitter containers (mid,right)
        self.main_splitter.setSizes([int(total_w * 0.6), int(total_w * 0.4)])

        self.main_layout.addWidget(self.main_splitter)
        self.top_bar.activate()

        self.setFocus()
        self.init_shortcuts()
        self.update()

    def clear_layout(self, layout):
        # If layout is not empty we delete his childrens
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
                elif item.layout():
                    self.clear_layout(item.layout())

    def clicked(self, event):
        if event.button == 1:
            self.click_pressed = True

    def no_clicked(self, event):
        if event.button == 1:
            self.click_pressed = False

    def get_max_coordinates(self):
        if self.data is not None:
            width = self.data.shape[0]
            height = self.data.shape[1]
            return width - 1, height - 1
        return 0, 0

    def cleanup_shortcuts(self):
        for s in self._shortcuts:
            s.setEnabled(False)
            s.deleteLater()
        self._shortcuts.clear()

    def update_time_from_up_key(self):
        if self.canvas is None or self.data is None:
            return

        current_t = self.canvas.current_t
        if current_t < self.canvas.max_t:
            if self.movie_timer.isActive():
                self.movie_timer.stop()
            next_t = current_t + 1
            self.slider_t.setValue(next_t)

    def update_time_from_down_key(self):
        if self.canvas is None or self.data is None:
            return

        current_t = self.canvas.current_t
        if current_t > 0:
            if self.movie_timer.isActive():
                self.movie_timer.stop()
            next_t = current_t - 1
            self.slider_t.setValue(next_t)

    def init_shortcuts(self):
        self.cleanup_shortcuts()
        shortcuts = {
            Qt.Key.Key_Left: self.toolbar.go_back,
            Qt.Key.Key_Right: self.toolbar.go_forward,
            Qt.Key.Key_Up: self.update_time_from_up_key,
            Qt.Key.Key_Down: self.update_time_from_down_key,
            Qt.Key.Key_Space: self.toggle_movie_mode,
            Qt.Key.Key_H: self.toolbar.home,
            Qt.Key.Key_Comma: self.toolbar.back,
            Qt.Key.Key_Period: self.toolbar.forward,
            Qt.Key.Key_Z: self.handle_zoom_key,
            Qt.Key.Key_M: self.handle_pan_key,
            Qt.Key.Key_F: self.toggle_fullscreen,
            "Ctrl+Z": self.go_to_previous_roi
        }
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def handle_zoom_key(self):
        if self.toolbar and not self.toolbar.mode.name == 'PAN' and not self.click_pressed:
            self.toolbar.zoom()

    def handle_pan_key(self):
        if self.toolbar and not self.toolbar.mode.name == 'ZOOM' and not self.click_pressed:
            self.toolbar.pan()

    def toggle_movie_mode(self):
        if self.movie_timer.isActive():
            self.movie_timer.stop()
        else:
            self.movie_timer.start(self.movie_speed)

    def next_movie_frame(self):
        if not self.canvas or self.data is None:
            return

        current_t = self.canvas.current_t
        total_points_time = self.data.shape[3]

        if current_t + 1 < total_points_time:
            next_t = current_t + 1
            self.slider_t.setValue(next_t)

        else:
            self.movie_timer.stop()
            self.slider_t.setValue(0)

    def update_main_canvas_by_time(self, index_t):
        """
        Update of the main canvas image with the T index
        :param index_t: Current T index of the slice that we want.
        :return: NiftiCanvas with the current T
        """
        # If we found the old Canvas, we put the slice we want to see
        if self.canvas:
            self.canvas.set_t(index_t)
            if index_t == 0 and self.movie_timer.isActive():
                self.movie_timer.stop()

    def update_graphic_by_input(self):
        if self.graphic:
            x = int(self.x.text())
            y = int(self.y.text())
            z = self.canvas.current_z
            intensities_t = self.data[x, y, z, :]
            self.graphic.update_graph(intensities_t, x, y)
            self.add_to_record(x, y, z, intensities_t)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def add_to_record(self, x, y, z, intensitis_t):
        intensity_increase = ((intensitis_t[-1] - intensitis_t[0]) / intensitis_t[0] * 100) if intensitis_t[
                                                                                                   0] != 0 else 0
        info = f"Click = {self.record_layout.count() + 1} | X = {x} | Y = {y} | Z = {z} | Intensity increase = {intensity_increase}"
        label = QLabel(info)
        # We add the info in the top of the layout
        self.record_layout.addWidget(label)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            if obj == self.slider_t or obj == self.slider_t_input:
                self.stop_movie_mode()

        return super().eventFilter(obj, event)

    def create_graphic(self, x, y, value):
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

        # We upload the graphic with the new data
        self.graphic.update_graph(intensities_t, x, y)
        self.x.blockSignals(True)
        self.y.blockSignals(True)
        self.x.setText(str(x))
        self.y.setText(str(y))
        self.x.blockSignals(False)
        self.y.blockSignals(False)

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
        # If we found the old Canvas, we put the slice we want to see
        if self.canvas:
            self.canvas.set_z(index_z)
            self.movie_timer.stop()  # We stop if we are in movie mode

    def normalize_img(self, img):
        """
        Function to normalize the intensity values img for display
        :param img: numpy array of data image
        :return: normalize numpy array data
        """
        # We normalize the image data to 0-255 range intensity
        if np.max(img) - np.min(img) != 0:
            norm_img = (img - np.min(img)) / (np.max(img) - np.min(img)) * 255
        else:
            # If the img has no contrast,return a black image
            norm_img = np.zeros_like(img)

        # Convert the data to unsigned 8-bit integer format for QImage compatibility
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

        # We normalize the img data
        norm_img = self.normalize_img(np.real(image_data))

        height, width = norm_img.shape
        bytes_per_line = width

        q_img = QImage(norm_img.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8).copy()
        pixmap = QPixmap.fromImage(q_img)
        image_container.setPixmap(pixmap)

        # We prepare the text of each slice
        label_text = QLabel(f"Slice {index + 1}")
        label_text.setStyleSheet("padding-top: 5px;")
        label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        vbox.addWidget(image_container)
        vbox.addWidget(label_text)

        # We add and event to each image to update the main image with this image z value
        image_container.image_clicked.connect(lambda: self.update_main_canvas_by_index_click(index))

        return container_widget

    def graphic_layout(self):
        """
        Creation of the layout that contains the graphic
        :return: the layout with the graphic created
        """
        container = QScrollArea()
        self.graphic = IntensityGraph()

        max_x, max_y = self.get_max_coordinates()

        self.input_x, self.x = self.input_label("Coor X", 0, max_x, 0, self.update_graphic_by_input)
        self.input_y, self.y = self.input_label("Coor Y", 0, max_y, 0, self.update_graphic_by_input)

        input_box = QHBoxLayout()
        input_box.addLayout(self.input_x)
        input_box.addLayout(self.input_y)

        layout = QVBoxLayout()
        layout.addLayout(input_box)
        layout.addSpacing(int(self.screen_size.height() * 0.01))
        layout.addWidget(self.graphic)

        # line to separate the graphic and the record
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #444;")
        layout.addWidget(line)

        scroll = QScrollArea()
        # scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scroll.setWidgetResizable(True)

        scroll_content = QWidget()
        self.record_layout = QVBoxLayout(scroll_content)
        self.record_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(scroll_content)

        layout.addWidget(QLabel("<b>Clicks record:</b>"))
        layout.addWidget(scroll)

        container.setMinimumWidth(int(self.screen_size.width() * 0.25))
        container.setMinimumHeight(
            int(self.screen_size.height() * 0.25))  # Test needing !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # main_container.setWidgetResizable(True)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # To prevent it from taking focus from the keyboard when it is clicked
        # main_container.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        container.setLayout(layout)

        container.setObjectName("graphic")

        return container

    def main_image_layout(self, data, subject_name):
        """
        Creation of the layout that contains the main/FigureCanvas image
        :param data: numpy array of data image
        :return: the layout with the main/FigureCanvas image inside
        """
        self.canvas = NiftiCanvas(data, subject_name)
        # No focus of the keyboard when pressed
        self.canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.canvas.mpl_connect('button_press_event', self.clicked)
        self.canvas.mpl_connect('button_release_event', self.no_clicked)

        # When clicked, create the graphic
        self.canvas.set_pixel_observer(self.create_graphic)

        # Toolbar with custom options
        self.toolbar = NiftiToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setMinimumSize(main_image_minSize)
        container.setMaximumWidth(int(self.screen_size.width() * 0.45))
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        container.setObjectName("main_image")

        container.setLayout(layout)

        self.toolbar.roi_menu.selected_text_signal.connect(self.change_roi_selector)
        self.toolbar.roi_menu.deactivate_roi_selection_signal.connect(self.deactivate_roi_selection)
        self.toolbar.previous_roi_signal.connect(self.go_to_previous_roi)

        return container

    def go_to_previous_roi(self):
        z_index = self.canvas.current_z
        if False not in self.full_mask[:, :, z_index]:
            return

        self.full_mask = restar_mask(self.full_mask, z_index)
        self.update_canvas_with_roi()

    def update_time_from_slider(self, t_value):
        """
        Updates the current T point and refreshes the UI with the slider
        :param t_value: selected T index
        """
        # We block the input signals to prevent a loop
        self.slider_t_input.blockSignals(True)
        self.slider_t_input.setText(str(t_value))
        self.slider_t_input.blockSignals(False)

        if self.canvas:
            self.canvas.set_t(t_value)

        if self.data is not None:
            # We update with the T value the images of the selector
            slices_t = get_nifti_slices(self.data, current_t=t_value)

    def update_time_from_text(self):
        """
        Updates the slider based on manual text input
        """
        text_val = self.slider_t_input.text()
        if text_val:
            new_t = int(text_val)
            self.slider_t.setValue(new_t)

            if self.movie_timer.isActive():
                self.movie_timer.stop()

    def update_fps_from_slider(self, fps_value):
        """
        Updates the current fps point and refreshes the UI with the slider
        :param fps_value: selected fps index
        """
        # We block the input signals to prevent a loop
        self.slider_fps_input.blockSignals(True)
        self.slider_fps_input.setText(str(fps_value))
        self.slider_fps_input.blockSignals(False)

        if fps_value > 0:
            self.movie_speed = int(1000 / fps_value)
        else:
            self.movie_speed = 1000

        if self.movie_timer.isActive():
            self.movie_timer.stop()

    def update_fps_from_text(self):
        """
        Updates the slider based on manual text input
        """
        text_val = self.slider_fps_input.text()
        if text_val:
            new_fps = int(text_val)
            self.slider_fps.setValue(new_fps)
            if self.movie_timer.isActive():
                self.movie_timer.stop()

    def stop_movie_mode(self):
        if self.movie_timer.isActive():
            self.movie_timer.stop()

    def input_label(self, input_text, min_range, max_range, init_val, text_callback):
        input_row_layout = QHBoxLayout()

        label = QLabel(f"<b>{input_text}:</b>")
        line_edit = QLineEdit(str(init_val))
        line_edit.setFixedWidth(35)
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        validator = QIntValidator(min_range, max_range, self)
        line_edit.setValidator(validator)

        def force_range(text):
            if text == "": return
            try:
                val = int(text)
                if val > max_range:
                    line_edit.setText(str(max_range))
                elif val < min_range:
                    pass
            except ValueError:
                pass

        line_edit.textChanged.connect(force_range)
        line_edit.editingFinished.connect(text_callback)

        input_row_layout.addStretch()
        input_row_layout.addWidget(label)
        input_row_layout.addWidget(line_edit)
        input_row_layout.addStretch()

        return input_row_layout, line_edit

    def slider_label(self, label_text, min_range, max_range, init_val, slider_callback, text_callback,
                     stop_movie=False):
        container_widget = QWidget()
        container_widget.setMinimumWidth(selector_minWidth)
        layout = QVBoxLayout(container_widget)

        input_row_layout = QHBoxLayout()

        label = QLabel(f"<b>{label_text}:</b>")
        line_edit = QLineEdit(str(init_val))
        line_edit.setFixedWidth(35)
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        validator = QIntValidator(min_range, max_range, self)
        line_edit.setValidator(validator)

        def force_range(text):
            if text == "": return
            try:
                val = int(text)
                if val > max_range:
                    line_edit.setText(str(max_range))
                elif val < min_range:
                    pass
            except ValueError:
                pass

        input_row_layout.addStretch()
        input_row_layout.addWidget(label)
        input_row_layout.addWidget(line_edit)
        input_row_layout.addStretch()

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_range)
        slider.setMaximum(max_range)
        slider.setValue(init_val)

        slider.valueChanged.connect(slider_callback)
        line_edit.textChanged.connect(force_range)
        line_edit.editingFinished.connect(text_callback)

        if stop_movie:
            slider.installEventFilter(self)
            line_edit.installEventFilter(self)

        layout.addLayout(input_row_layout)
        layout.addWidget(slider)

        return container_widget, slider, line_edit

    def update_image_selector(self, images_data):
        # We clean the selector
        self.clear_layout(self.selector_layout)

        # For each image in the data, we create a row according to the quantity we specify
        for i in range(0, len(images_data), amount_image_selector_in_row):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            # From the beginning of this row to the indicated amount
            row_images = images_data[i:i + amount_image_selector_in_row]

            for j, current_image in enumerate(row_images):
                global_index = i + j
                image = self.selector_image_creation(current_image, image_in_selector_maxSize, global_index)
                row_layout.addWidget(image)
                row_layout.addSpacing(50)

            if len(row_images) < amount_image_selector_in_row:
                for _ in range(amount_image_selector_in_row - len(row_images)):
                    spacer = QWidget()
                    spacer.setFixedSize(image_in_selector_maxSize)
                    row_layout.addWidget(spacer, 0)
                    row_layout.addSpacing(50)

            self.selector_layout.addWidget(row_widget)

    def image_selector_layout(self, images_data):
        """
        Function to create the image selector layout
        :param images_data: array of data nifti image
        :return: QScroll with all the images
        """
        main_left_widget = QWidget()
        main_left_widget.setFixedWidth(selector_minWidth)
        main_left_layout = QVBoxLayout(main_left_widget)
        main_left_layout.setContentsMargins(0, 0, 0, 0)

        num_t_points = self.data.shape[3] if self.data is not None else 1

        slider_t_group, self.slider_t, self.slider_t_input = self.slider_label(
            "Time Point (T)", 0, num_t_points - 1, 0,
            self.update_time_from_slider, self.update_time_from_text, True
        )

        slider_fps_group, self.slider_fps, self.slider_fps_input = self.slider_label(
            "FPS", 1, 60, 30,
            self.update_fps_from_slider, self.update_fps_from_text
        )

        main_left_layout.addWidget(slider_t_group)
        main_left_layout.addWidget(slider_fps_group)

        container = QWidget()
        self.selector_layout = QVBoxLayout(container)
        self.selector_layout.setSpacing(30)
        self.selector_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.update_image_selector(images_data)

        scroll = QScrollArea()
        scroll.setMinimumWidth(selector_minWidth)
        scroll.setWidgetResizable(True)
        # deactivation of the horizontal bar
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("selector")
        scroll.setWidget(container)
        main_left_layout.addWidget(scroll)

        return main_left_widget

    def create_rectangle_selector(self):
        ax = self.canvas.axes

        self.current_roi = RectangleSelector(ax, self.on_rectangle_select,
                                             useblit=False,
                                             button=[1],
                                             minspanx=5, minspany=5,
                                             spancoords='data',
                                             interactive=True)

    def create_elliptical_selector(self):
        ax = self.canvas.axes

        self.current_roi = EllipseSelector(ax, self.on_ellipsis_select,
                                           # 'line' To see the border
                                           useblit=True,
                                           button=[1],  # left button of the mouse
                                           minspanx=5, minspany=5,
                                           spancoords='pixels',
                                           interactive=True)

    def on_rectangle_select(self, eclick, erelease):
        roi_coords = (eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata)
        z_index = self.canvas.current_z
        self.full_mask = create_rectangular_mask(roi_coords, self.full_mask, z_index)
        self.update_canvas_with_roi()

    def update_mask_history(self):
        self.mask_history.append(self.full_mask)
        self.current_mask_counter += 1

    def on_ellipsis_select(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        xc = (x1 + x2) / 2
        yc = (y1 + y2) / 2
        a = abs(x2 - x1) / 2
        b = abs(y2 - y1) / 2

        ellipsis_center = (xc, yc)
        radius = (a, b)

        z_index = self.canvas.current_z
        # full_mask, ellipsis_center, radius, z_index
        self.full_mask = update_elliptical_mask_subtractive(self.full_mask, ellipsis_center, radius, z_index)
        # self.update_mask_history(mask)
        self.update_canvas_with_roi()

    def get_current_slice(self):
        return self.data[:, :, self.canvas.current_z, 0]

    def update_canvas_with_roi(self):

        roi4d_array = self.original_data * self.full_mask[:, :, :, np.newaxis]
        roi_slices_t0 = [roi4d_array[:, :, z, 0].T for z in range(roi4d_array.shape[2])]

        self.data = roi4d_array

        QTimer.singleShot(1, lambda: self.update_widgets(roi_slices_t0))

    def update_widgets(self, roi_slices_t0):
        if self.current_roi:
            self.current_roi.set_visible(False)
            if self.canvas:
                self.canvas.draw_idle()

        if self.left_container:
            self.update_image_selector(np.array(roi_slices_t0))
        else:
            self.left_container = self.image_selector_layout(np.array(roi_slices_t0))

            if self.main_splitter:
                self.main_splitter.insertWidget(0, self.left_container)

        if self.canvas:
            self.canvas.update_image(self.data)

    def change_roi_selector(self, selected_roi):
        self.selected_roi = selected_roi
        match selected_roi:
            case "r":
                self.create_rectangle_selector()
            case "e":
                self.create_elliptical_selector()

    def deactivate_roi_selection(self):
        self.current_roi = None

    def receive_file_list(self, files):
        if files:
            file_path = [str(Path(files)) for files in files]
            self.file_list.addItems(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    logo_path = os.path.join(name_current_dir, "assets", "logo.png")
    app.setWindowIcon(QIcon(logo_path))
    # app.setStyle(QStyleFactory.create("Fusion"))
    window = MainWindow()

    window.show()
    sys.exit(app.exec())
