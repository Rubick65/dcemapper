from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox


class AlertDialog(QDialog):
    WINDOW_WIDTH = 150
    WINDOW_HEIGHT = 100

    def __init__(self, title, message, buttons: bool = False, parent=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.buttons = buttons
        self.setWindowTitle(self.title)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.initUi()

    def initUi(self):
        vertical_layout = QVBoxLayout(self)
        vertical_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        vertical_layout.addStretch()

        message_label = QLabel(text=self.message)
        message_label.setStyleSheet("font-size: 20px;")

        vertical_layout.addWidget(message_label, alignment=Qt.AlignmentFlag.AlignCenter)

        if self.buttons:
            button_box = self.create_button_box()
            vertical_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)

        vertical_layout.addStretch()

        self.setLayout(vertical_layout)

    def change_alert_text(self, title, message):
        self.title = title
        self.message = message

    def create_button_box(self):
        buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        button_box = QDialogButtonBox(buttons)

        button_box.accepted.connect(self.accepted)
        button_box.rejected.connect(self.reject)

        return button_box


def init_alert_visual(title, message):
    alert_visual = AlertDialog(title, message)
    alert_visual.show()
    alert_visual.raise_()
