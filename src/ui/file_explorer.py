import sys
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidget, QGridLayout, QWidget, \
    QToolBar, QVBoxLayout


class TopBar(QToolBar):
    files_selected = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        file_button_action = QAction("Open File", self)
        file_button_action.setStatusTip("Open File")
        file_button_action.triggered.connect(self.open_file_dialog)
        self.addAction(file_button_action)

    def open_file_dialog(self):
        dialog = QFileDialog(self)

        dialog.setDirectory(r'C:\images')
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        # dialog.setNameFilter("Images (*.png *.jpg)")
        dialog.setViewMode(QFileDialog.ViewMode.List)

        if dialog.exec():
            filenames = dialog.selectedFiles()
            if filenames:
                self.files_selected.emit(filenames)


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

        self.main_layout = QVBoxLayout(self.centralWidget)

        self.top_bar = TopBar()
        self.file_list = FileListWidget()

        self.addToolBar(self.top_bar)
        self.main_layout.addWidget(self.file_list)

        self.top_bar.files_selected.connect(self.update_list)

    def initUI(self):
        # Main window configuration
        self.main_window_configurations()

        layout = QGridLayout()
        self.setLayout(layout)

    def main_window_configurations(self):
        main_window_width = 1200
        main_window_height = 600

        self.setWindowTitle("File explorer test")
        self.resize(main_window_width, main_window_height)

    def update_list(self, files):
        file_path = [str(Path(files)) for files in files]
        self.file_list.addItems(file_path)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
