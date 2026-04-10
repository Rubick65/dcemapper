import os
import sys
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap, QImage, QKeySequence, QShortcut, QIntValidator
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QScrollArea, QLabel, \
    QSizePolicy, QSlider, QLineEdit, QSplitter
from matplotlib.widgets import RectangleSelector, EllipseSelector, PolygonSelector

from src.io.nifti_io import load_nifti, get_nifti_slices
from src.preprocessing.denoise.denoise_filter import denoise_init_one_file
from src.preprocessing.gibbs_removal.gibbs_removal import gibbs_remove
from src.roi.roi_creation import update_rectangular_mask, update_elliptical_mask, update_polygon_mask, restar_mask
from src.ui.Images_Class.ClickImage import ClickImage
from src.ui.Images_Class.IntensityGraph import IntensityGraph
from src.ui.Images_Class.NiftiCanvas import NiftiCanvas
from src.ui.file_explorer.file_explorer import TopMenu
from src.ui.interface.NiftiToolbar import NiftiToolbar
from src.utils.utils import create_output_folder, get_correct_subject, normalize_img, UserCancelledError

# -----------------CONSTANTS-----------------
window_minSize = QSize(1125, 500)

image_in_selector_maxSize = QSize(90, 90)
selector_maxWidth = 480
selector_minWidth = 200
main_image_minSize = QSize(300, 400)

name_current_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QMainWindow):

    def __init__(self, nifty_path=None):
        super().__init__()
        self.file_list = None
        self.setWindowTitle("dcemapper")
        self.setMinimumSize(window_minSize)
        self.screen_size = self.screen().availableGeometry()  # Window size
        width = int(self.screen_size.width() * 0.825)
        height = int(self.screen_size.height() * 0.85)
        self.total_w = self.width()
        self.total_h = self.height()
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
        self.amount_image_selector_in_row = 2
        self.image_widgets = []
        self.current_columns = 0
        self.mid_container = None
        self.right_container = None

        self.main_splitter = None

        self.current_roi = None
        self.roi_coords = None
        self.vertices = None
        self.ellipsis_center = None
        self.radius = None
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

    def next_movie_frame(self):
        """
        To advance the T of the nifti image at the set frame rate
        """
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

    def set_various_files(self, nifty_data):
        nifty_path, derivative_folder = nifty_data
        if isinstance(nifty_path, tuple):
            self.current_subject = nifty_path[0]  # Name of the subject
            nifty_path = nifty_path[1]
        else:
            # If it is a single file, we extract the subject name from the file structure
            self.current_subject = get_correct_subject(Path(nifty_path))

        self.derivative_folder = derivative_folder

        self.set_nifti(nifty_path)

        self.check_for_preprocessed_file(nifty_path)

    def check_for_preprocessed_file(self, file):
        file_name = Path(file).name
        if "preproc" in file_name:
            self.toolbar.roi_menu.activate_roi_selection()

    def preprocessing(self, selected_preprocess_options):
        denoise_filter, gibbs = selected_preprocess_options

        output_folder = create_output_folder(self.current_subject if self.current_subject else "Unknown",
                                             self.derivative_folder)
        data = self.nifty_path
        try:
            if denoise_filter:
                data = denoise_init_one_file(self.nifty_path, output_folder, denoise_filter)
        except UserCancelledError:
            print()

        if gibbs:
            data = gibbs_remove([data])

        self.nifty_path = data

        self.data, _ = load_nifti(data)
        self.original_data = self.data
        self.toolbar.roi_menu.activate_roi_selection()

        roi_slices = get_nifti_slices(self.data)
        self.update_widgets(roi_slices)

        self.top_bar.file_menu.change_current_file(data)

    def update_widgets(self, roi_slices_t0):

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

    def update_image_selector(self, images_data):

        # If is the first time that we create the selector
        if not self.image_widgets or len(self.image_widgets) != len(
                images_data) or self.current_columns != self.amount_image_selector_in_row:

            self.current_columns = self.amount_image_selector_in_row
            self.image_widgets = []
            self.clear_layout(self.selector_layout)

            for i in range(0, len(images_data), self.amount_image_selector_in_row):
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)

                row_images = images_data[i:i + self.amount_image_selector_in_row]

                for j, current_image in enumerate(row_images):
                    global_index = i + j
                    container, img_widget = self.selector_image_creation(current_image, image_in_selector_maxSize,
                                                                         global_index)
                    self.image_widgets.append(img_widget)
                    row_layout.addWidget(container)
                    row_layout.addStretch()

                self.selector_layout.addWidget(row_widget)

        # If the left container it was already created, we update the images instead of creating them
        else:
            for i, current_image in enumerate(images_data):
                img_widget = self.image_widgets[i]
                norm_img = normalize_img(np.real(current_image))
                height, width = norm_img.shape
                q_img = QImage(norm_img.tobytes(), width, height, QImage.Format.Format_Grayscale8).copy()
                pixmap = QPixmap.fromImage(q_img)
                img_widget.setPixmap(pixmap)

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
        norm_img = normalize_img(np.real(image_data))

        height, width = norm_img.shape
        bytes_per_line = width

        q_img = QImage(norm_img.tobytes(), width, height, bytes_per_line, QImage.Format.Format_Grayscale8).copy()
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

        return container_widget, image_container

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

    def set_nifti(self, nifty_path):
        """
        Function to load al the componets in the interface with the data
        :param nifty_path: Nifti image path
        :return: Creation of the data interface
        """
        if nifty_path == "":
            return

        self.stop_movie_mode()

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

        self.image_widgets = []

        self.nifty_path = nifty_path
        self.data, _ = load_nifti(self.nifty_path)
        self.original_data = self.data.copy()
        self.full_mask = np.ones(self.data.shape[:3], dtype=float)

        # We clean the layout
        self.clear_layout(self.main_layout)

        # Splitter to drag the mid and right containers sizes
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create all the containers
        self.left_container = self.image_selector_layout(get_nifti_slices(self.data))
        self.mid_container = self.main_image_layout(self.data, self.current_subject)
        self.right_container = self.graphic_layout()

        self.main_splitter.addWidget(self.left_container)
        self.main_splitter.addWidget(self.mid_container)
        self.main_splitter.addWidget(self.right_container)

        # To prevent that the containers collapse each to other
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, False)
        self.main_splitter.setCollapsible(2, False)

        # Sizes of splitter containers (mid,right)
        self.main_splitter.setSizes([int(self.total_w * 0.2), int(self.total_w * 0.4), int(self.total_w * 0.4)])

        self.main_layout.addWidget(self.main_splitter)
        self.top_bar.activate()

        self.setFocus()
        self.init_shortcuts()
        self.update()

    def stop_movie_mode(self):
        if self.movie_timer.isActive():
            self.movie_timer.stop()

    def get_max_coordinates(self):
        if self.data is not None:
            width = self.data.shape[0]
            height = self.data.shape[1]
            return width - 1, height - 1
        return 0, 0

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

    def image_selector_layout(self, images_data):
        """
        Function to create the image selector layout
        :param images_data: array of data nifti image
        :return: QScroll with all the images
        """
        main_left_widget = QWidget()
        main_left_widget.setMaximumWidth(selector_maxWidth)
        main_left_widget.setMinimumWidth(selector_minWidth)
        main_left_layout = QVBoxLayout(main_left_widget)
        main_left_layout.setContentsMargins(0, 0, 0, 0)

        num_t_points = self.data.shape[3] if self.data is not None else 1

        # Creation of the T and fps sliders

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
        scroll.setMaximumWidth(selector_maxWidth)
        scroll.setMinimumWidth(selector_minWidth)
        scroll.setWidgetResizable(True)

        # deactivation of the horizontal bar
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(container)
        main_left_layout.addWidget(scroll)
        main_left_widget.installEventFilter(self)

        return main_left_widget

    def slider_label(self, label_text, min_range, max_range, init_val, slider_callback, text_callback,
                     stop_movie=False):
        """
        Creation of a slider label with your texts.
        :param label_text: label text
        :param min_range: min range of the slider
        :param max_range: max range of the slider
        :param init_val: initial value of the slider
        :param slider_callback: function called when the slider moves
        :param text_callback: function called when the text is entered in the input
        :param stop_movie: bool to know if we stop the movie mode or not
        :return: the slider label, the line edit and his container
        """
        container_widget = QWidget()
        container_widget.setMinimumWidth(selector_minWidth)
        container_widget.setMaximumWidth(selector_maxWidth)
        layout = QVBoxLayout(container_widget)

        input_row_layout = QHBoxLayout()

        label = QLabel(f"<b>{label_text}:</b>")
        line_edit = QLineEdit(str(init_val))
        line_edit.setFixedWidth(35)
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        validator = QIntValidator(min_range, max_range, self)
        line_edit.setValidator(validator)

        def force_range(text):
            """
            Internal function to validate that the established limits are not exceeded
            :param text: input text
            :return: value modified to respect the limits
            """
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

        # Functions that are activated when a value is modified
        slider.valueChanged.connect(slider_callback)
        line_edit.textChanged.connect(force_range)
        line_edit.editingFinished.connect(text_callback)

        if stop_movie:
            slider.installEventFilter(self)
            line_edit.installEventFilter(self)

        layout.addLayout(input_row_layout)
        layout.addWidget(slider)

        return container_widget, slider, line_edit

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


    def update_time_from_text(self):
        """
        Updates the slider based on manual text input
        """
        text_val = self.slider_t_input.text()
        if text_val:
            new_t = int(text_val)
            self.slider_t.setValue(new_t)
            self.stop_movie_mode()

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

        self.stop_movie_mode()

    def update_fps_from_text(self):
        """
        Updates the slider based on manual text input
        """
        text_val = self.slider_fps_input.text()
        if text_val:
            new_fps = int(text_val)
            self.slider_fps.setValue(new_fps)
            self.stop_movie_mode()

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
        layout.setContentsMargins(0, 20, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setMinimumSize(main_image_minSize)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # To prioritize focus on this window whenever possible
        container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        container.setLayout(layout)

        self.toolbar.roi_menu.selected_text_signal.connect(self.change_roi_selector)
        self.toolbar.roi_menu.deactivate_roi_selection_signal.connect(self.deactivate_roi_selection)
        self.toolbar.previous_roi_signal.connect(self.go_to_previous_roi)
        container.installEventFilter(self)

        return container

    def create_graphic(self, x, y, value):
        """
        Upload of the graphic with the pixel data
        :param x: coorX of the pixel image
        :param y: coorY of the pixel image
        :return: Upload of the graphic
        """
        current_z = self.canvas.current_z
        intensities_t = self.data[x, y, current_z, :]
        self.add_to_record(x, y, current_z, intensities_t)

        # We upload the graphic with the new data
        self.graphic.update_graph(intensities_t, x, y)
        # Block the signals to prevent errors
        self.x.blockSignals(True)
        self.y.blockSignals(True)
        self.x.setText(str(x))
        self.y.setText(str(y))
        self.x.blockSignals(False)
        self.y.blockSignals(False)

    def add_to_record(self, x, y, z, intensitis_t):
        """
        Function to add the intensities to the record
        :param x: Coor X
        :param y: Coor Y
        :param z: current Slice (Z)
        :param intensitis_t: Intensities in all the times
        """
        intensity_increase = ((intensitis_t[-1] - intensitis_t[0]) / intensitis_t[0] * 100) if intensitis_t[
                                                                                                   0] != 0 else 0
        info = f"Click = {self.record_layout.count() + 1} | X = {x} | Y = {y} | Z = {z} | Intensity increase = {intensity_increase}"
        label = QLabel(info)
        # We add the info in the top of the layout
        self.record_layout.addWidget(label)

    def change_roi_selector(self, selected_roi):
        self.selected_roi = selected_roi
        self.clear_current_roi()
        match selected_roi:
            case "r":
                self.create_rectangle_selector()
            case "e":
                self.create_elliptical_selector()
            case "p":
                self.create_polygon_selector()

    def clear_current_roi(self):
        if self.current_roi is not None:
            self.current_roi.set_active(False)
            self.current_roi.set_visible(False)
            self.current_roi = None
            self.canvas.draw_idle()

    def create_rectangle_selector(self):
        ax = self.canvas.axes

        self.current_roi = RectangleSelector(ax, self.on_rectangle_select,
                                             useblit=True,
                                             button=[1],
                                             minspanx=5, minspany=5,
                                             spancoords='pixels',
                                             interactive=True, props=dict(color="cyan", fill=False))

    def on_rectangle_select(self, eclick, erelease):
        self.roi_coords = (eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata)

    def create_elliptical_selector(self):
        ax = self.canvas.axes

        self.current_roi = EllipseSelector(ax, self.on_ellipsis_select,
                                           useblit=True,
                                           button=[1],
                                           minspanx=5, minspany=5,
                                           spancoords='pixels',
                                           interactive=True, props=dict(color="cyan", fill=False))

    def on_ellipsis_select(self, eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        xc = (x1 + x2) / 2
        yc = (y1 + y2) / 2
        a = abs(x2 - x1) / 2
        b = abs(y2 - y1) / 2

        self.ellipsis_center = (xc, yc)
        self.radius = (a, b)

    def create_polygon_selector(self):
        ax = self.canvas.axes
        style_config = dict(
            color='cyan',
            linestyle='-',
            linewidth=1,
            alpha=0.5
        )

        self.current_roi = PolygonSelector(ax, self.on_polygon_select,
                                           useblit=True, props=style_config)

    def on_polygon_select(self, vertices):
        self.vertices = vertices

    def deactivate_roi_selection(self):
        self.clear_current_roi()

    def go_to_previous_roi(self):
        z_index = self.canvas.current_z
        if False not in self.full_mask[:, :, z_index]:
            return

        self.full_mask = restar_mask(self.full_mask, z_index)
        self.update_canvas_with_roi()

    def update_canvas_with_roi(self):

        roi4d_array = self.original_data * self.full_mask[:, :, :, np.newaxis]
        roi_slices_t0 = [roi4d_array[:, :, z, 0].T for z in range(roi4d_array.shape[2])]

        self.data = roi4d_array

        QTimer.singleShot(1, lambda: self.update_widgets(roi_slices_t0))

    def graphic_layout(self):
        """
        Creation of the container that holds the graph, with its inputs and the click log
        :return: The container with its components
        """
        container = QScrollArea()
        container.setWidgetResizable(True)
        container.setMinimumWidth(int(self.screen_size.width() * 0.325))

        content_widget = QWidget()
        main_v_layout = QVBoxLayout(content_widget)

        self.graphic = IntensityGraph()
        self.graphic.setMinimumHeight(400)
        max_x, max_y = self.get_max_coordinates()

        # Creation of the X and Y inputs
        input_container_widget = QWidget()
        self.input_x, self.x = self.input_label("Coor X", 0, max_x, 0, self.update_graphic_by_input)
        self.input_y, self.y = self.input_label("Coor Y", 0, max_y, 0, self.update_graphic_by_input)

        input_box_layout = QHBoxLayout(input_container_widget)
        input_box_layout.addLayout(self.input_x)
        input_box_layout.addLayout(self.input_y)

        # Splitter to drag and drop elements while resizing them
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        v_splitter.addWidget(self.graphic)

        record_group_widget = QWidget()
        record_group_widget.installEventFilter(self)
        record_v_layout = QVBoxLayout(record_group_widget)
        record_v_layout.setContentsMargins(0, 5, 0, 0)

        # Line to separate graph and record (visual only)
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #444;")
        record_v_layout.addWidget(line)
        record_v_layout.addWidget(QLabel("<b>Clicks record:</b>"))

        scroll_record = QScrollArea()
        scroll_record.setWidgetResizable(True)
        scroll_content = QWidget()
        self.record_layout = QVBoxLayout(scroll_content)
        self.record_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_record.setWidget(scroll_content)

        record_v_layout.addWidget(scroll_record)

        v_splitter.addWidget(record_group_widget)

        v_splitter.setSizes([int(self.total_h * 0.7), int(self.total_h * 0.3)])

        v_splitter.setCollapsible(0, False)

        main_v_layout.addWidget(input_container_widget)
        main_v_layout.addWidget(v_splitter)

        container.setWidget(content_widget)
        container.installEventFilter(self)

        return container

    def input_label(self, input_text, min_range, max_range, init_val, text_callback):
        """
        Function to create input fields with your texts.
        :param input_text: input text
        :param min_range: min range of the input
        :param max_range: max range of the input
        :param init_val: initial value of the input
        :param text_callback: Function called when the text is entered
        :return: the input label and the line edit
        """
        input_row_layout = QHBoxLayout()

        label = QLabel(f"<b>{input_text}:</b>")
        line_edit = QLineEdit(str(init_val))
        line_edit.setFixedWidth(35)
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        validator = QIntValidator(min_range, max_range, self)
        line_edit.setValidator(validator)

        def force_range(text):
            """
            Internal function to validate that the established limits are not exceeded
            :param text: input text
            :return: value modified to respect the limits
            """
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

    def update_graphic_by_input(self):
        if self.graphic:
            x = int(self.x.text())
            y = int(self.y.text())
            z = self.canvas.current_z
            intensities_t = self.data[x, y, z, :]
            self.graphic.update_graph(intensities_t, x, y)
            self.add_to_record(x, y, z, intensities_t)

    def init_shortcuts(self):
        """
        To clear and create keyboard shortcuts every time a file is opened
        """
        self.cleanup_shortcuts()
        shortcuts = {
            Qt.Key.Key_Left: self.toolbar.go_back,
            Qt.Key.Key_Right: self.toolbar.go_forward,
            Qt.Key.Key_Up: self.update_time_from_up_key,
            Qt.Key.Key_Down: self.update_time_from_down_key,
            Qt.Key.Key_Space: self.toggle_movie_mode,
            Qt.Key.Key_H: self.toolbar.home,
            Qt.Key.Key_R: self.reset_layout,
            Qt.Key.Key_Comma: self.toolbar.back,
            Qt.Key.Key_Period: self.toolbar.forward,
            Qt.Key.Key_Z: self.handle_zoom_key,
            Qt.Key.Key_M: self.handle_pan_key,
            Qt.Key.Key_F: self.toggle_fullscreen,
            "Ctrl+Z": self.go_to_previous_roi,
            "Ctrl+R": self.rectangle_mode,
            "Ctrl+E": self.elliptical_mode,
            "Ctrl+P": self.polygon_mode,
            Qt.Key.Key_Escape: self.cancel_roi,
            Qt.Key.Key_Tab: self.save_roi_state,
        }
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def cleanup_shortcuts(self):
        """
        Deleting previous shortcuts to avoid errors
        """
        for s in self._shortcuts:
            s.setEnabled(False)
            s.deleteLater()
        self._shortcuts.clear()

    def update_time_from_up_key(self):
        if self.canvas is None or self.data is None:
            return

        current_t = self.canvas.current_t
        if current_t < self.canvas.max_t:
            self.stop_movie_mode()
            next_t = current_t + 1
            self.slider_t.setValue(next_t)

    def update_time_from_down_key(self):
        if self.canvas is None or self.data is None:
            return

        current_t = self.canvas.current_t
        if current_t > 0:
            self.stop_movie_mode()
            next_t = current_t - 1
            self.slider_t.setValue(next_t)

    def toggle_movie_mode(self):
        if self.movie_timer.isActive():
            self.movie_timer.stop()
        else:
            self.movie_timer.start(self.movie_speed)

    def reset_layout(self):
        """
        Reset of the default sizes of each container
        """
        if self.main_splitter:
            self.main_splitter.setSizes([int(self.total_w * 0.2), int(self.total_w * 0.4), int(self.total_w * 0.4)])
        try:
            v_splitters = self.right_container.findChildren(QSplitter)
            for vs in v_splitters:
                if vs.orientation() == Qt.Orientation.Vertical:
                    vs.setSizes([int(self.total_h * 0.7), int(self.total_h * 0.3)])  # Size of graphic and record layout
        except Exception:
            pass

    def handle_zoom_key(self):
        if self.toolbar and not self.toolbar.mode.name == 'PAN' and not self.click_pressed:
            self.toolbar.zoom()

    def handle_pan_key(self):
        if self.toolbar and not self.toolbar.mode.name == 'ZOOM' and not self.click_pressed:
            self.toolbar.pan()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def cancel_roi(self):
        if self.current_roi and self.current_roi.get_visible():
            self.current_roi.set_visible(False)
            self.current_roi.set_visible(True)

            self.current_roi.clear()

    def save_roi_state(self):
        if self.current_roi and self.current_roi.get_visible():
            self.calculate_selected_roi()
            self.update_canvas_with_roi()
            self.cancel_roi()

    def calculate_selected_roi(self):
        z_index = self.canvas.current_z

        if self.selected_roi == "":
            return

        match self.selected_roi:
            case "r":
                self.full_mask = update_rectangular_mask(self.roi_coords, self.full_mask, z_index)
                self.roi_coords = None
            case "e":
                self.full_mask = update_elliptical_mask(self.full_mask, self.ellipsis_center, self.radius, z_index)
                self.ellipsis_center = None
                self.radius = None
            case "p":
                self.full_mask = update_polygon_mask(self.full_mask, self.vertices, z_index)
                self.vertices = None

    def rectangle_mode(self):
        if self.toolbar.roi_menu.already_processed:
            self.toolbar.roi_menu.activate_roi_by_prefix("r")

    def elliptical_mode(self):
        if self.toolbar.roi_menu.already_processed:
            self.toolbar.roi_menu.activate_roi_by_prefix("e")

    def polygon_mode(self):
        if self.toolbar.roi_menu.already_processed:
            self.toolbar.roi_menu.activate_roi_by_prefix("p")

    def clicked(self, event):
        if event.button == 1:
            self.click_pressed = True

    def no_clicked(self, event):
        if event.button == 1:
            self.click_pressed = False

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            if obj == self.slider_t or obj == self.slider_t_input:
                self.stop_movie_mode()

        if event.type() == event.Type.Resize:
            self.stop_movie_mode()
            if obj == self.left_container:
                self.adjust_selector_columns()

        return super().eventFilter(obj, event)

    def adjust_selector_columns(self):
        """
        To adjust the number of images per row in the selector,
        widen the selection to make the most of the available space.
        """
        if self.data is None or self.selector_layout is None:
            return

        current_width = self.left_container.width()

        new_amount = max(1, current_width // 110)

        if new_amount != self.amount_image_selector_in_row and new_amount % 2 == 0:
            self.amount_image_selector_in_row = new_amount
            roi_slices = get_nifti_slices(self.data)
            self.update_image_selector(roi_slices)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    logo_path = os.path.join(name_current_dir, "assets", "logo.png")
    app.setWindowIcon(QIcon(logo_path))
    # app.setStyle(QStyleFactory.create("Fusion"))
    window = MainWindow()

    window.show()
    sys.exit(app.exec())
