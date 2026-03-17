import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QApplication, QDialogButtonBox, QVBoxLayout, QLabel, \
    QHBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

RETRY_CODE = 2


class PreprocessingCanvas(FigureCanvas):
    MIN_WIDTH = 500
    MIN_HEIGHT = 300

    MAX_WIDTH = 800
    MAX_HEIGHT = 500

    def __init__(self, figure, parent=None):
        super().__init__(figure)
        self.setParent(parent)

        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.fig = figure


class PreprocessingVisual(QDialog):

    def __init__(self, figure, retry=True, parent=None, question_label_text="Are you happy with the results?"):
        super().__init__(parent)
        self.question_label_text = question_label_text
        self.figure = figure
        self.toolbar = None
        self.retry = retry
        self.initUI()

    def initUI(self):
        self.show_options()

    def show_options(self):
        v_layout = QVBoxLayout()
        v_layout.setSpacing(25)

        h_layout = QHBoxLayout()

        sc = PreprocessingCanvas(self.figure, self)
        self.toolbar = NavigationToolbar(sc, self)

        question_label = QLabel(self.question_label_text)
        question_label.setStyleSheet("font-size: 20px; font-weight: plain")
        button_box = self.create_buttonBox()

        h_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)

        v_layout.addStretch()
        v_layout.addWidget(self.toolbar, alignment=Qt.AlignmentFlag.AlignLeft)
        v_layout.addWidget(sc, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(question_label, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addLayout(h_layout)

        v_layout.addStretch()

        self.setLayout(v_layout)

    def create_buttonBox(self):

        QBtn = self.create_buttons()
        button_box = QDialogButtonBox(QBtn)
        button_box.layout().setSpacing(20)

        if self.retry:
            retry_btn = button_box.button(QDialogButtonBox.StandardButton.Retry)
            retry_btn.clicked.connect(lambda: self.done(2))
        else:
            button_box = QDialogButtonBox(QBtn)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        return button_box

    def create_buttons(self):
        if self.retry:
            return (
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Retry
            )
        else:
            return (
                QDialogButtonBox.StandardButton.Ok
            )


def init_view(figure, retry):
    app = QApplication.instance() or QApplication(sys.argv)
    window = PreprocessingVisual(figure, retry)

    response_code = window.exec()

    if response_code == QDialog.DialogCode.Accepted:
        result = False
    elif response_code == RETRY_CODE:
        result = True
    else:
        result = False

    return result


def main():
    app = QApplication(sys.argv)
    window = PreprocessingVisual()
    window.exec()


if __name__ == "__main__":
    main()
