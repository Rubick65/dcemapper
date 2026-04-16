import os

import nibabel as nib
import numpy as np

from src.io.nifti_io import load_nifti
from src.utils.utils import create_general_preprocess_output
from src.visualization.filter_visualization import ask_user_parameters


def semi_quantitative(data, img, folders: tuple, semi_quantitative_data: tuple = None):
    retry = True
    while (retry):
        frame_ini_contrast, frame_period = get_semi_quantitative_data(semi_quantitative_data)

        output_folder = folders[0]
        nifti_file_path = folders[1]

        reference_value = calculate_reference_value(data, frame_ini_contrast)

        rce = calculate_rce(data, reference_value)

        retry = create_general_preprocess_output(data, rce, "Processed")

    save_nifit(rce, img.affine, output_folder, nifti_file_path)


def get_semi_quantitative_data(semi_quantitative_data: tuple):
    if semi_quantitative_data:
        return semi_quantitative_data[0], semi_quantitative_data[1]
    else:
        default_quantitative_data = {
            "Frame Init Contrast": [10, "Frame period for calculating RCE"],
            "Frame Period": [12.8, "Period between frames"]
        }

        semi_quantitative_data = ask_user_parameters(default_quantitative_data, "Semi Quantitative")

        return semi_quantitative_data["Frame Init Contrast"], semi_quantitative_data["Frame Period"]


def calculate_reference_value(data, n_pixeles):
    first_frame = data[:, :, :, 0]
    important_pixels = first_frame[first_frame > 10]

    selection_pixel = important_pixels[:n_pixeles]

    return np.mean(selection_pixel)


def save_nifit(data, affine, output_folder, nifti_file_path):
    img = nib.Nifti1Image(data, affine)

    denoised_nii_name = os.path.basename(nifti_file_path).replace(
        ".nii.gz", "_proc.nii.gz"
    )
    denoised_nii_output_path = os.path.join(
        output_folder, denoised_nii_name
    )

    nib.save(img, denoised_nii_output_path)


def calculate_rce(data, reference_value):
    rce = np.zeros_like(data)
    mask = data > 0

    rce[mask] = ((data[mask] - reference_value) / reference_value) * 100

    return rce


def calculate_rce_max():
    pass


def main():
    data, img = load_nifti(
        r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\sub-B060326_WTF1_d10_DCE_acq-10_run-1_dce.nii.gz")

    semi_quantitative(data, img,
                      (r"C:\Users\laboratorio\PycharmProjects\dcemapper\src",
                       r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\sub-B060326_WTF1_d10_DCE_acq-10_run-1_dce.nii.gz"))


if __name__ == "__main__":
    main()
