import sys
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidget, QGridLayout, QWidget, \
    QVBoxLayout, QMenuBar, QMenu

from src.utils.misc import denoise_filters_dict, file_options_dict


class NonePersistentMenu(QMenu):

    def leaveEvent(self, a0):
        if self.underMouse():
            return

        active_action = self.activeAction()
        if active_action and active_action.menu() and active_action.menu().isVisible():
            return

        super().hide()


class PersistentMenu(NonePersistentMenu):

    def mouseReleaseEvent(self, event):
        """
        Overrides default mouse release action, new action
        only hides the menu when
        :param event:
        :return:
        """
        # Gets the action at its position
        action = self.actionAt(event.pos())

        # When the action is done in a Persistan Menu option
        if action and action.isCheckable():
            # The normal action is triggered
            action.trigger()
        else:
            # If the click is outside, the menu hides
            super().mouseReleaseEvent(event)


class PreprocessingMenu(PersistentMenu):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.create_preprocessing_menu()

    def create_preprocessing_menu(self):
        """
        Creates preprocessing menu section
        :return: None
        """

        # Create preprocessing actions
        preprocessing_actions = self.create_preprocessing_menus()

        # Create preprocessing menu
        self.setTitle("&Preprocessing")
        # Tracks mouse
        self.setMouseTracking(True)
        # Adds actions to preprocessing menu
        self.addActions(preprocessing_actions)

    def create_preprocessing_menus(self) -> tuple:
        """
        Creates preprocessing actions
        :returns a tuple with all the preprocessing actions
        """
        denoise_menu = DenoiseMenu(self)
        self.addMenu(denoise_menu)

        # Gibbs artifact suppression
        gibbs_artifact_suppression = QAction("&Gibbs artifact suppression", self)
        gibbs_artifact_suppression.setStatusTip("Gibbs artifact suppression")
        gibbs_artifact_suppression.setCheckable(True)

        # Bias field correction
        bias_field_correction = QAction("&Bias field correction", self)
        bias_field_correction.setStatusTip("Bias field correction")
        bias_field_correction.setCheckable(True)

        return gibbs_artifact_suppression, bias_field_correction


class DenoiseMenu(PersistentMenu):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.denoising_filters = []
        self.group = QActionGroup(self)
        self.group.setExclusive(False)
        self.initMenu()

    def initMenu(self):
        self.setTitle("&Denoising")
        self.denoising_filter_actions()
        self.group.triggered.connect(self.handle_exclusivity)

    def denoising_filter_actions(self):
        for action, status_tip in denoise_filters_dict.items():
            denoising_filter = QAction(action, self)
            denoising_filter.setStatusTip(status_tip)
            denoising_filter.setCheckable(True)

            self.group.addAction(denoising_filter)
            self.addAction(denoising_filter)

            self.denoising_filters.append(denoising_filter)

    def handle_exclusivity(self, selected_action):
        if selected_action.isChecked():
            for action in self.group.actions():
                if action is not selected_action:
                    action.setChecked(False)


class FileMenu(PersistentMenu):
    # Signal for the selected files
    file_signal = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.denoising_filters = []
        self.group = QActionGroup(self)
        self.group.setExclusive(False)
        self.initMenu()

    def initMenu(self):
        self.setTitle("&File")
        self.file_actions()
        self.group.triggered.connect(self.open_file_action)

    def file_actions(self):
        for action, status_tip in file_options_dict.items():
            file_options = QAction(action, self)
            file_options.setStatusTip(status_tip)

            self.group.addAction(file_options)
            self.addAction(file_options)

            self.denoising_filters.append(file_options)

    def open_file_action(self, selected_action):
        selected_action_text = selected_action.text().split(" ")[1][0:1].lower()

        self.different_file_options(selected_action_text)

    def file_selector(self):
        """
        Opens PyQt6 file explorer and emits a signal with the path
        to the selected files
        :return: Path or paths with the selected files
        """
        # Widget for file explorer
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)

        # Indicates the original directory
        dialog.setDirectory(r'C:\Users\laboratorio\PycharmProjects\dcemapper')
        # Only shows existing files
        dialog.setFileMode(QFileDialog.FileMode.Directory)

        # Filter only for indicated files
        # dialog.setNameFilter("('.nii.gz', '.nii')")
        # Detailed mode
        dialog.setViewMode(QFileDialog.ViewMode.Detail)

        # if file explorer widget is executed
        if dialog.exec():
            # Stores selected files
            files = dialog.selectedFiles()
            # If files exists
            if files:
                # Emits a signal with the path to the files
                self.file_signal.emit(files)

    def different_file_options(self, selected_option):
        match selected_option:
            case "n":
                self.file_selector()


class TopMenu(QMenuBar):
    visible = True

    def __init__(self):
        super().__init__()
        self.file_menu = FileMenu(self)
        self.preprocessing_menu = PreprocessingMenu(self)
        self.create_top_menu()

    def create_top_menu(self):
        # File menu with all the options
        self.addMenu(self.file_menu)

        # Preprocessing menu section
        self.addMenu(self.preprocessing_menu)


class FileListWidget(QListWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

        # Create the central widget for the file list
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.top_menu = TopMenu()

        self.main_layout = QVBoxLayout(self.centralWidget)

        self.file_list = FileListWidget()
        self.main_layout.addWidget(self.file_list)

        self.setMenuBar(self.top_menu)
        self.top_menu.file_menu.file_signal.connect(self.receive_file_list)

    def initUI(self):
        # Main window configuration
        self.main_window_configurations()

        layout = QGridLayout(self)
        self.setLayout(layout)

    def receive_file_list(self, files):
        if files:
            file_path = [str(Path(files)) for files in files]
            self.file_list.addItems(file_path)

    def main_window_configurations(self):
        main_window_width = 1200
        main_window_height = 600

        self.setWindowTitle("File explorer test")
        self.resize(main_window_width, main_window_height)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
