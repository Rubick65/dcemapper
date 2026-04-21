import numpy as np
from matplotlib import pyplot as plt

from src.io.nifti_io import load_nifti
from src.utils.utils import create_general_preprocess_output, save_output_nifti, normalize_img
from src.visualization.filter_visualization import ask_user_parameters

mask = None


def semi_quantitative(data, img, folders: tuple, semi_quantitative_data: tuple = None):
    # Indicates if the user wants to retry for parameter selection
    retry = True

    # While retry is true
    while retry:
        # Get´s the data needed for semi quantitative processing
        frame_ini_contrast, frame_period = get_semi_quantitative_data(semi_quantitative_data)

        output_folder = folders[0]
        nifti_file_path = folders[1]

        reference_value = calculate_reference_value(data, frame_ini_contrast)

        rce = calculate_rce(data, reference_value)

        rce_max = get_rce_max_value(rce)

        retry = create_general_preprocess_output(data, rce, "Processed")

    rce_save = save_output_nifti(rce, img.affine, output_folder, nifti_file_path,"rce_proc")

    rce_max_save = save_output_nifti(rce_max, img.affine, output_folder, nifti_file_path,"rce_max_proc")

    tto_rce_max_save = save_output_nifti(tto_rce_max, img.affine, output_folder, nifti_file_path, "tto_rce_max")

    return rce_save, rce_max_save, tto_rce_max_save


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


def get_rce_max_value(rce):
    return np.max(rce, axis=3)


def get_ttp_rce_max_value(rce, frame_period):

    max_index = np.argmax(rce, axis=3)

    time_to_peak = max_index * frame_period

    tto_rce_max = np.where(mask, time_to_peak, 0)

    ttp_norm = normalize_img(tto_rce_max)

    norm_img = (ttp_norm * 255).astype(np.uint8)

    return norm_img


def calculate_reference_value(data, frame_ini_contrast):
    S0 = np.mean(data[:, :, :, :frame_ini_contrast,], axis=3)

    return S0


def calculate_rce(data, reference_value):
    global mask
    data = data.astype(np.float32)
    s0 = reference_value.astype(np.float32)

    mask = s0 > (np.mean(s0) * 0.3)

    s0_expanded = s0[:, :, :, np.newaxis]
    mask_expanded = mask[:, :, :, np.newaxis]

    rce = np.where(mask_expanded,
                   ((data - s0_expanded) / s0_expanded) * 100,
                   0)

    rce = np.clip(rce, 0, 500)

    return rce


def main():
    data, img = load_nifti(
        r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\sub-B060326_WTF1_d10_DCE_acq-10_run-1_dce.nii.gz")

    semi_quantitative(data, img,
                      (r"C:\Users\laboratorio\PycharmProjects\dcemapper\src",
                       r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\sub-B060326_WTF1_d10_DCE_acq-10_run-1_dce_preproc.nii.gz"))


if __name__ == "__main__":
    main()
