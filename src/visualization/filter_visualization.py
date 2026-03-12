import sys
import tkinter as tk

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QPushButton, QMainWindow, QApplication, QDialogButtonBox, QVBoxLayout, QLabel, \
    QLineEdit


class UserParameterDialog(QDialog):
    input_params = {}

    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)
        self.parameter_dict = {
            "patch_size": [3, "Size of patches used for denoising."],
            "patch_distance": [7, "Maximal search distance (pixels)."],
            "h": [4.5, "Cut-off distance (in gray levels)."],
        }
        self.initUI()

    def initUI(self):
        self.setWindowTitle("dcemapper")

        self.parameters_selection_dialog(self.parameter_dict)

    def parameters_selection_dialog(self, parameter_dict):
        vertical_layout = QVBoxLayout()
        button_box = self.create_button_box()

        vertical_layout.setSpacing(15)
        vertical_layout.addStretch()

        for parameter, info in parameter_dict.items():
            label_text = QLabel(text=f"[{parameter}]: {info[1]}")
            vertical_layout.addWidget(label_text, alignment=Qt.AlignmentFlag.AlignCenter)

            input_param = QLineEdit()
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
                self.input_params[parameter] = value

            except (ValueError, TypeError):
                self.input_params[parameter].setText(f"Invalid input for {parameter}!")
                submit = False

        if submit:
            self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")

        button = QPushButton("Press me for a dialog!")
        button.clicked.connect(self.button_clicked)
        self.setCentralWidget(button)

    def button_clicked(self, s):
        dlg = UserParameterDialog()
        dlg.exec()


def ask_user_parameters(parameter_dict):
    """Select values for different parameters in an emergent window. If a new value is
    selected it has to be of the same class as the predetermined value.

    Args:
        parameter_dict (dict): Dictionary containing the name of the different
            parameters as keys, along with a list containing the predetermined value for
            each one and a brief description.

    Returns:
        dict: Dictionary containing the selected values for each parameter name.
    """
    root = tk.Tk()
    root.title("resomapper")

    values = {}

    def submit():
        nonlocal values

        for parameter, info in parameter_dict.items():
            value = entry_boxes[parameter].get()
            predetermined_value = info[0]
            value_type = type(predetermined_value)
            try:
                if value_type is bool:
                    # For boolean types, check if the input is 'True' or 'False'
                    value = str(value).lower()
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
                error_label.config(text=f"Invalid input for {parameter}!")
                return

        root.destroy()
        root.quit()

    entry_boxes = {}
    for parameter, info in parameter_dict.items():
        label_text = f"[{parameter}] {info[1]}"
        label = tk.Label(root, text=label_text)
        label.pack(padx=50, pady=(10, 0))
        entry_box = tk.Entry(root)
        entry_box.insert(0, info[0])  # Set predetermined value as default
        entry_box.pack()
        entry_boxes[parameter] = entry_box

    error_label = tk.Label(root, text="", fg="red")
    error_label.pack()

    submit_button = tk.Button(root, text="OK", command=submit)
    submit_button.pack(pady=20)

    root.mainloop()
    try:
        return values
    except NameError:
        # TODO: change to raise specific error or check if this is neccesary
        print(
            f"\n\nYou have not selected any parameters. Exiting the program."
        )
        exit()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
