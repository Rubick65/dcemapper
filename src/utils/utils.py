import os
from tkinter import filedialog
import tkinter as tk

def is_valid_nifti(path):
    if not path.endswith(('.nii.gz', '.nii')):
        raise ValueError('Not a valid nifti file')


def is_folder_and_not_occult(path):
    return (
            (os.path.isdir(path))
            and not os.path.basename(path).startswith(".")
    )


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
