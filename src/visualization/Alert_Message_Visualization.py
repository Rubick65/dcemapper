import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication


class AlertDialog(QDialog):

    WINDOW_WIDTH = 150
    WINDOW_HEIGHT = 100

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.initUi(message)

    def initUi(self, message):
        vertical_layout = QVBoxLayout(self)
        vertical_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        vertical_layout.addStretch()

        message_label = QLabel(text=message)
        message_label.setStyleSheet("font-size: 20px;")

        vertical_layout.addWidget(message_label, alignment=Qt.AlignmentFlag.AlignCenter)

        vertical_layout.addStretch()

        self.setLayout(vertical_layout)


def main():
    app = QApplication(sys.argv)
    window = AlertDialog("Alert Message", "There is no created mask, please create one.")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
