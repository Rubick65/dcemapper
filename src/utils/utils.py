import os

import matplotlib

from src.visualization.filter_visualization import ask_user_parameters

matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
import numpy as np
import shutil as shutil
from src.visualization.preprocessing_visualization import init_view

class UserCancelledError(Exception):
    pass

def is_valid_nifti(path):
    if not path.endswith(('.nii.gz', '.nii')):
        raise ValueError('Not a valid nifti file')


def is_folder_and_not_occult(path):
    return (
            (os.path.isdir(path))
            and not os.path.basename(path).startswith(".")
    )


def info_and_ask_denoising_params(filter_name, params):
    """Print a message indicating the selected filter and ask the user to input the
    neccesary parameters.

    Args:
        filter_name (str): Name of the selected filter.
        params (dict): Dictionary containing the parameter names along with a list
            that contains the predetermined value and a brief description

    Returns:
        dict: Dictionary containing the selected values for each parameter name.
    """
    return ask_user_parameters(params, filter_name)


def create_general_preprocess_output(original_image, denoised_image, output_text, last_text="Residuals", retry=True):
    """Display the denoised output and residuals of the denoising process.

    This method takes the original image and its denoised counterpart and displays
    them side by side along with the residual image obtained by computing
    the element-wise squared difference between the original and denoised images.
    A middle slice is shown.

    Args:
        original_image (numpy.ndarray): The original 3D or 4D image to be denoised.
        denoised_image (numpy.ndarray): The denoised version of the original image.

    Returns:
        bool: A boolean value indicating whether the user wants to change the
            denoising parameters.
    """

    sli = original_image.shape[2] // 2

    if len(original_image.shape) == 3:
        orig = original_image[:, :, sli]
        den = denoised_image[:, :, sli]
        gra = "-"
    else:
        gra = original_image.shape[3] // 2
        orig = original_image[:, :, sli, gra]
        den = denoised_image[:, :, sli, gra]

    # compute the residuals
    rms_diff = np.sqrt((orig - den) ** 2)

    fig1, ax = plt.subplots(
        1, 3, figsize=(12, 6), subplot_kw={"xticks": [], "yticks": []}
    )

    fig1.subplots_adjust(hspace=0.3, wspace=0.05)
    fig1.suptitle(f"Sample of residuals (slice {sli}, subslice {gra})")

    ax.flat[0].imshow(orig.T, cmap="gray", interpolation="none")
    ax.flat[0].set_title("Original")
    ax.flat[1].imshow(den.T, cmap="gray", interpolation="none")
    ax.flat[1].set_title(f"{output_text} Output")
    ax.flat[2].imshow(rms_diff.T, cmap="gray", interpolation="none")
    ax.flat[2].set_title(f"{last_text}")

    return init_view(fig1, retry)


def show_bias_field_correction_ask(original_image, corrected_image, log_bias_field):
    sli = original_image.shape[2] // 2

    if len(original_image.shape) == 3:
        orig = original_image[:, :, sli]
        den = corrected_image[:, :, sli]
        biasf = log_bias_field[:, :, sli]
        gra = "-"
    else:
        gra = original_image.shape[2] // 2
        orig = original_image[:, :, sli, gra]
        den = corrected_image[:, :, sli, gra]
        if len(log_bias_field.shape) == 3:
            biasf = log_bias_field[:, :, sli]
        else:
            biasf = log_bias_field[:, :, sli, gra]

    fig1, ax = plt.subplots(
        1, 3, figsize=(12, 6), subplot_kw={"xticks": [], "yticks": []}
    )

    fig1.subplots_adjust(hspace=0.3, wspace=0.05)
    fig1.suptitle(f"Sample of bias-field corrected image (slice {sli}, subslice {gra})")

    ax.flat[0].imshow(orig.T, cmap="gray", interpolation="none")
    ax.flat[0].set_title("Original")
    ax.flat[1].imshow(den.T, cmap="gray", interpolation="none")
    ax.flat[1].set_title("Corrected")
    ax.flat[2].imshow(biasf.T, cmap="gray", interpolation="none")
    ax.flat[2].set_title("Bias field")

    return init_view(fig1)


def rename_associated_files(nifti_filename):
    """
    Rename files after being preprocessed
    :param nifti_filename: Name of the nifti file
    :return:
    """
    # If preproc is in the nifti file name
    if "_preproc" in nifti_filename:
        # Get´s the different files
        json_file = nifti_filename.replace("_preproc.nii.gz", ".json")
        bval_file = nifti_filename.replace("_preproc.nii.gz", ".bval")
        bvec_file = nifti_filename.replace("_preproc.nii.gz", ".bvec")
        for associated_file in [json_file, bval_file, bvec_file]:
            if os.path.exists(associated_file):
                shutil.copy(
                    associated_file,
                    nifti_filename.replace("nii.gz", associated_file.split(".")[-1]), )


def is_nii(filename):
    """
    Check if a file is a valid NifTi
    :param filename: Name of the file
    :return: True if is a valid NifTi file, False otherwise
    """
    if not isinstance(filename, str):
        filename = str(filename)

    return filename.endswith(".nii") or filename.endswith(".nii.gz")


def create_output_folder(subject, derivatives_folder):
    """
    Creat derivatives folder
    :param subject: Subject ID for naming the folder
    :param derivatives_folder: Where derivatives are saved
    :return: Path to the output folder
    """
    output_folder = os.path.join(derivatives_folder, subject)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    return output_folder


def get_correct_subject(file):
    current_file = file.name
    for i in range(3):
        file = file.parent
        current_file = file.name
        if "sub" in current_file:
            return current_file
    else:
        return current_file


def normalize_img(img):
    """
    Function to normalize the intensity values img for display
    :param img: numpy array of data image
    :return: normalize numpy array data
    """
    # We normalize the image data to 0-255 range intensity
    if np.max(img) - np.min(img) != 0:
        norm_img = (img - np.min(img)) / (np.max(img) - np.min(img)) * 255
    else:
        # If the img has no contrast,return a black image
        norm_img = np.zeros_like(img)

    # Convert the data to unsigned 8-bit integer format for QImage compatibility
    norm_img = norm_img.astype(np.uint8)
    return norm_img
