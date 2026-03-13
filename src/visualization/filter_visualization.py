import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QApplication, QDialogButtonBox, QVBoxLayout, QLabel, \
    QLineEdit


class ClickLabel(QLineEdit):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class UserParameterDialog(QDialog):
    input_params = {}
    value_signal = {}

    def __init__(self, parameter_dict):
        super().__init__()
        self.parameter_dict = parameter_dict
        self.initUI()

    def initUI(self):
        self.setWindowTitle("dcemapper")

        self.parameters_selection_dialog(self.parameter_dict)

    def parameters_selection_dialog(self, parameter_dict):
        vertical_layout = QVBoxLayout(self)
        button_box = self.create_button_box()

        vertical_layout.addStretch()

        vertical_layout.setContentsMargins(35, 35, 35, 35)

        vertical_layout.setSpacing(15)

        vertical_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        for parameter, info in parameter_dict.items():
            label_text = QLabel(text=f"[{parameter}]: {info[1]}")
            vertical_layout.addWidget(label_text, alignment=Qt.AlignmentFlag.AlignCenter)

            input_param = ClickLabel()
            input_param.setFixedSize(150, 30)
            input_param.setText(str(info[0]))
            vertical_layout.addWidget(input_param, alignment=Qt.AlignmentFlag.AlignCenter)
            self.input_params[parameter] = input_param

        vertical_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)

        vertical_layout.addStretch()

        self.setLayout(vertical_layout)

    def create_button_box(self) -> QDialogButtonBox:
        QBtn = (
            QDialogButtonBox.StandardButton.Save
        )
        button_box = QDialogButtonBox(QBtn)
        button_box.accepted.connect(self.submit)

        return button_box

    def submit(self):
        submit = True
        values = {}
        for parameter, info in self.parameter_dict.items():

            value = self.input_params[parameter].text()
            predetermined_value = info[0]
            value_type = type(predetermined_value)
            try:
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

        if submit:
            self.value_signal = values
            self.accept()

    def remove_invalid_input_text(self):
        input_text = self.sender()
        
        if input_text:
            input_text.clear()
            input_text.setStyleSheet("")
            input_text.clicked.disconnect()


def ask_user_parameters(parameter_dict):
    app = QApplication.instance() or QApplication(sys.argv)
    window = UserParameterDialog(parameter_dict)

    if window.exec() == QDialog.DialogCode.Accepted:
        return window.value_signal
    else:
        return {key: val[0] for key, val in parameter_dict.items()}
