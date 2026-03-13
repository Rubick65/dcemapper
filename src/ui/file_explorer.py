import sys
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidget, QGridLayout, QWidget, \
    QVBoxLayout, QMenuBar, QMenu, QAbstractItemView


class NonePersistentMenu(QMenu):

    def leaveEvent(self, a0):
        if not self.underMouse():
            super().hide()


class PersistentMenu(QMenu):

    def mouseReleaseEvent(self, event):
        action = self.actionAt(event.pos())
        if action and action.isCheckable():
            action.trigger()
        else:
            super().mouseReleaseEvent(event)

    def leaveEvent(self, a0):
        if not self.underMouse():
            super().hide()


class TopMenu(QMenuBar):
    # Signal for the select files
    file_signal = pyqtSignal(list)

    visible = True

    def __init__(self):
        super().__init__()
        self.create_top_menu()

    def create_top_menu(self):
        # File menu with all the options
        self.create_file_menu()

        # Preprocessing menu section
        self.create_preprocessing_menu()

    def create_file_menu(self):
        open_file_action = self.create_open_file_action()

        # Add file option to the menu
        none_persistent_menu = PersistentMenu("&File", self)
        none_persistent_menu.addAction(open_file_action)
        self.addMenu(none_persistent_menu)

    def create_open_file_action(self) -> QAction:
        # Opening file action
        open_file_action = QAction("&Open File", self)
        open_file_action.setStatusTip("This is your button")
        open_file_action.triggered.connect(self.open_file_triggered)

        return open_file_action

    def create_preprocessing_menu(self):

        preprocessing_actions = self.create_preprocessing_action()

        persistent_menu = PersistentMenu("&Preprocessing", self)
        persistent_menu.setMouseTracking(True)
        persistent_menu.addActions(preprocessing_actions)
        self.addMenu(persistent_menu)

    def create_preprocessing_action(self) -> tuple:

        denoising_filter = QAction("&Denoising", self)
        denoising_filter.setStatusTip("Denoising filter")
        denoising_filter.setCheckable(True)

        gibbs_artifact_suppression = QAction("&Gibbs Artifact Suppression", self)
        gibbs_artifact_suppression.setStatusTip("Gibbs artifact suppression")
        gibbs_artifact_suppression.setCheckable(True)

        bias_field_correction = QAction("&Bias Field Correction", self)
        bias_field_correction.setStatusTip("Bias field correction")
        bias_field_correction.setCheckable(True)

        return denoising_filter, gibbs_artifact_suppression, bias_field_correction

    def open_file_triggered(self):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)

        dialog.setDirectory(r'C:\home')
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        dialog.setNameFilter("('.nii.gz', '.nii')")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if dialog.exec():
            files = dialog.selectedFiles()
            if files:
                self.file_signal.emit(files)


class FileListWidget(QListWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

        # Create the central widget for the file list
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.top_menu = TopMenu()

        self.main_layout = QVBoxLayout(self.centralWidget)

        self.file_list = FileListWidget()
        self.main_layout.addWidget(self.file_list)

        self.setMenuBar(self.top_menu)
        self.top_menu.file_signal.connect(self.receive_file_list)

        # self.open_file_action.files_selected.connect(self.update_list)

    def initUI(self):
        # Main window configuration
        self.main_window_configurations()

        layout = QGridLayout()
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
