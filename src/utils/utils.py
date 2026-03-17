import os

import matplotlib

from src.visualization.filter_visualization import ask_user_parameters

matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from IPython.display import clear_output
import numpy as np
import shutil as shutil
from src.visualization.preprocessing_visualization import init_view


def is_valid_nifti(path):
    if not path.endswith(('.nii.gz', '.nii')):
        raise ValueError('Not a valid nifti file')


def is_folder_and_not_occult(path):
    return (
            (os.path.isdir(path))
            and not os.path.basename(path).startswith(".")
    )


# Callback invoked when the StartEvent happens, sets up our new data.
def start_register_plot():
    global metric_values, multires_iterations

    metric_values = []
    multires_iterations = []


# Callback invoked when the EndEvent happens, do cleanup of data and figure.
def end_register_plot():
    global metric_values, multires_iterations

    del metric_values
    del multires_iterations
    # Close figure, we don't want to get a duplicate of the plot latter on.
    plt.close()


# Callback invoked when the IterationEvent happens, update our data and display new figure.
def plot_register_values(registration_method):
    global metric_values, multires_iterations

    metric_values.append(registration_method.GetMetricValue())
    # Clear the output area (wait=True, to reduce flickering), and plot current data
    clear_output(wait=True)
    # Plot the similarity metric values
    plt.plot(metric_values, 'r')
    plt.plot(multires_iterations, [metric_values[index] for index in multires_iterations], 'b*')
    plt.xlabel('Iteration Number', fontsize=12)
    plt.ylabel('Metric Value', fontsize=12)
    plt.show()


# Callback invoked when the sitkMultiResolutionIterationEvent happens, update the index into the
# metric_values list.
def update_multires_iterations():
    global metric_values, multires_iterations
    multires_iterations.append(len(metric_values))


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


def create_general_preprocess_output(original_image, denoised_image, output_text, last_text="Residuals", retry = True ):
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
    if "_preproc" in nifti_filename:
        json_file = nifti_filename.replace("_preproc.nii.gz", ".json")
        bval_file = nifti_filename.replace("_preproc.nii.gz", ".bval")
        bvec_file = nifti_filename.replace("_preproc.nii.gz", ".bvec")
        for associated_file in [json_file, bval_file, bvec_file]:
            if os.path.exists(associated_file):
                shutil.copy(
                    associated_file,
                    nifti_filename.replace("nii.gz", associated_file.split(".")[-1]), )
