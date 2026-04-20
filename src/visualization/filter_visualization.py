import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QApplication, QDialogButtonBox, QVBoxLayout, QLabel, \
    QLineEdit


class ClickLabel(QLineEdit):
    # Signal when click is pressed
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        """
        Overrides mousePress event
        :param event: Normal event when mouse is pressed
        :return: None
        """
        # Emit a signal when label is clicked
        self.clicked.emit()
        # Then do the normal click event
        super().mousePressEvent(event)


class UserParameterDialog(QDialog):

    def __init__(self, parameter_dict, filter_name):
        """
        Initialize user parameter dialog for select preprocess parameters
        :param parameter_dict: Dictionary with preprocess parameters to show
        :param filter_name: Name of the selected preprocess filter
        """
        super().__init__()
        # Dict with the input params
        self.input_params = {}
        self.value_signal = {}
        self.parameter_dict = parameter_dict
        self.filter_name = filter_name
        self.initUI()

    def initUI(self):
        """
        Initialize the UI of the parameter selection dialog
        :return: None
        """
        self.setWindowTitle("dcemapper")

        # Create the UI
        self.parameters_selection_dialog(self.parameter_dict)

    def parameters_selection_dialog(self, parameter_dict):
        """
        Creates preprocess window dialog
        :param parameter_dict: Parameter dict with the parameters to show
        :return: None
        """

        # Main layout(vertical)
        vertical_layout = QVBoxLayout(self)
        # Box for the buttons
        button_box = self.create_button_box()

        # Adds stretch before adding all the widgets
        vertical_layout.addStretch()

        # Margins between widgets
        vertical_layout.setContentsMargins(35, 35, 35, 35)

        # Spacing between widgets
        vertical_layout.setSpacing(15)

        # Ensure the layout's parent widget respects the minimum size of its content
        vertical_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        # Label with filter name text
        label_title = QLabel(f"{self.filter_name.capitalize()}")
        label_title.setStyleSheet("font-size: 20px; font-weight: bold")

        # Add label title to vertical layout
        vertical_layout.addWidget(label_title, alignment=Qt.AlignmentFlag.AlignCenter)

        # For every parameter in the dict
        for parameter, info in parameter_dict.items():
            # Create a label with the paramete and the info to show
            label_text = QLabel(f"[{parameter}]: {info[1]}")

            # Add info text to vertical layout
            vertical_layout.addWidget(label_text, alignment=Qt.AlignmentFlag.AlignCenter)

            # Input widget for user to change parameters
            input_param = ClickLabel()
            input_param.setFixedSize(150, 30)
            input_param.setText(str(info[0]))

            # Add input param to vertical layout
            vertical_layout.addWidget(input_param, alignment=Qt.AlignmentFlag.AlignCenter)
            # Add the input param to the dict of parameters
            self.input_params[parameter] = input_param

        # Add button box to vertical layout
        vertical_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add stretch after all the widget are added
        vertical_layout.addStretch()

        # Set vertical layout as main layout
        self.setLayout(vertical_layout)

    def create_button_box(self) -> QDialogButtonBox:
        """
        Create the button box widget
        :return: Button box with the needed buttons
        """
        buttons = QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel

        button_box = QDialogButtonBox(buttons)

        button_box.accepted.connect(self.submit)
        button_box.rejected.connect(self.reject)

        return button_box

    def submit(self):
        """
        Check if input params are valid and emit signal to continue
        :return: None
        """
        # If the params are correct
        submit = True
        values = {}
        # For every item in parameter dict
        for parameter, info in self.parameter_dict.items():
            # Get the text of the input param
            value = self.input_params[parameter].text()
            # Get predetermined value of the param
            predetermined_value = info[0]
            # Get the type of the predetermined value
            value_type = type(predetermined_value)
            try:
                # If the value type is boolean
                if value_type is bool:
                    # For boolean types, check if the input is 'True' or 'False'
                    value = value.lower()
                    if value in ["true", "1"]:
                        value = True
                    elif value in ["false", "0"]:
                        value = False
                    else:
                        raise ValueError
                else:
                    value = value_type(value)

                if value_type is str and not value:
                    raise ValueError
                values[parameter] = value

            except (ValueError, TypeError):
                error_input = self.input_params[parameter]
                error_input.setText(f"Invalid input!")
                error_input.setStyleSheet("color: red; font-size: 10px; font-weight: bold")

                try:
                    error_input.clicked.disconnect()
                except TypeError:
                    pass

                error_input.clicked.connect(self.remove_invalid_input_text)
                submit = False

        # If submit is True
        if submit:
            # Values of the selected params
            self.value_signal = values
            # Emit accept signal
            self.accept()

    def remove_invalid_input_text(self):
        """
        Remove invalid input text
        :return: None
        """

        # Get input widget that sent the signal
        input_text = self.sender()

        # If input text is not none
        if input_text:
            # First clear the input text
            input_text.clear()
            # Then remove all the style
            input_text.setStyleSheet("")
            # Finally clicked event is disconnected
            input_text.clicked.disconnect()

    def reject(self):
        self.value_signal = None
        super().reject()

def ask_user_parameters(parameter_dict: dict, filter_name: str):
    app = QApplication.instance() or QApplication(sys.argv)
    window = UserParameterDialog(parameter_dict, filter_name)
    app.setQuitOnLastWindowClosed(False)

    if window.exec() == QDialog.DialogCode.Accepted:
        param = window.value_signal
        window.deleteLater()
        return param
    else:
        window.deleteLater()
        return None