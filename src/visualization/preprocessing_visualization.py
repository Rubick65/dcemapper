import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QApplication, QDialogButtonBox, QVBoxLayout, QLabel, \
    QHBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

RETRY_CODE = 2


class PreprocessingCanvas(FigureCanvas):
    # Min Size of the preprocessing window
    MIN_WIDTH = 500
    MIN_HEIGHT = 300

    # Max Size of the preprocessing window
    MAX_WIDTH = 800
    MAX_HEIGHT = 500

    def __init__(self, figure, parent=None):
        """
        Initialize windget canvas with the preprocessed figure
        :param figure: Selected figure that is going to be shown in the window
        :param parent: Parent widget
        """
        super().__init__(figure)
        self.setParent(parent)

        # Minimum size of the figure widget
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Maximum size of the figure widget
        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.fig = figure


class PreprocessingVisual(QDialog):
    """
    Popup window for showing preprocessed data
    """

    def __init__(self, figure, data, retry=True, parent=None, question_label_text="Are you happy with the results?"):
        """
        Initialize preprocessing visual window
        :param figure: Figure that is going to be shown in the window
        :param data: numpy array of the figure
        :param retry: If retry option is active or not
        :param parent: Indicates the parent widget
        :param question_label_text: Text that is going to be shown to the user
        """
        super().__init__(parent)
        self.question_label_text = question_label_text
        self.figure = figure
        self.toolbar = None
        self.retry = retry
        self.data = data

        self.initUI()

    def initUI(self):
        """
        Initialize the UI
        :return: None
        """
        self.show_preprocessing_view()

    def show_preprocessing_view(self):
        """
        Shows the preprocessed figure in the window
        :return: None
        """

        # Main Layout(Vertical)
        v_layout = QVBoxLayout()
        v_layout.setSpacing(25)

        # Horizontal layout
        h_layout = QHBoxLayout()

        # Creates the widget with the figure
        sc = PreprocessingCanvas(self.figure, self)

        # Create the toolbar widget for the figure
        self.toolbar = NavigationToolbar(sc, self)

        # Create the text shown in the window
        question_label = QLabel(self.question_label_text)
        question_label.setStyleSheet("font-size: 20px; font-weight: plain")

        # Create the necessary buttons
        button_box = self.create_buttonBox()

        # Add the button box to horizontal layout
        h_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add stretch to the top part
        v_layout.addStretch()

        # First add the toolbar, figure, text and horizontal box with button box
        v_layout.addWidget(self.toolbar, alignment=Qt.AlignmentFlag.AlignLeft)
        v_layout.addWidget(sc, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(question_label, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addLayout(h_layout)

        # Add stretch to the bottom part
        v_layout.addStretch()

        # Sets the main layout for the window(Vertical layout)
        self.setLayout(v_layout)

    def create_buttonBox(self):
        """
        Creates button box depending on the retry option
        :return: None
        """

        # Creates the necessary buttons
        QBtn = self.create_buttons()
        # Creates the box with the buttons
        button_box = QDialogButtonBox(QBtn)
        # Sets spacing between buttons
        button_box.layout().setSpacing(20)

        # if retry is active
        if self.retry:
            # Get the retry button
            retry_btn = button_box.button(QDialogButtonBox.StandardButton.Retry)
            # When retry is pressed signal is emitted with code 2
            retry_btn.clicked.connect(lambda: self.done(2))
        else:
            # If not, button box is created
            button_box = QDialogButtonBox(QBtn)

        # When any button is pressed a code is emitted
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        return button_box

    def create_buttons(self):
        """
        Creates necessary buttons
        :return: None
        """
        # If retry is active
        if self.retry:
            # All buttons are created
            return (
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Retry
            )
        else:
            # Only Ok button is created
            return (
                QDialogButtonBox.StandardButton.Ok
            )


def init_view(figure, retry, data):
    """
    Initialize the preprocessing visualization window
    :param figure: Figure that is going to be shown in the window
    :param retry: If retry option is active or not
    :param data: numpy array of the figure
    :return: Boolean, indicating if the user wants to retry or not
    """
    # Creation of the app
    app = QApplication.instance() or QApplication(sys.argv)
    # Creation of the window instance
    window = PreprocessingVisual(figure, data, retry)
    # Execute the window and get the response code
    response_code = window.exec()

    # Depending on the response code
    if response_code == QDialog.DialogCode.Accepted:
        # If Ok is pressed
        restart = False
    elif response_code == RETRY_CODE:
        # If retry is pressed
        restart = True
    else:
        # If the window is closed
        restart = False

    return restart
