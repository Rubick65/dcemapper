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
