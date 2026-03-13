import os

import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import SimpleITK as sitk

from dipy.core.gradients import gradient_table
from dipy.denoise.adaptive_soft_matching import adaptive_soft_matching
from dipy.denoise.localpca import localpca, mppca
from dipy.denoise.nlmeans import nlmeans
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.patch2self import patch2self
from dipy.denoise.pca_noise_estimate import pca_noise_estimate
from dipy.denoise.gibbs import gibbs_removal
from nibabel.testing import data_path

from src.io.nfti_loader import load_nifti
from src.visualization.filter_visualization import ask_user_parameters

# TODO: if we remove one of the nlmeans maybe this to remove one dependency
from skimage.restoration import denoise_nl_means


def denoise():
    example_file = os.path.join(data_path, 'example4d.nii.gz')
    data, affine = load_nifti(example_file)


    img, _ = mp_pca_denoising(data,None)

    show_denoised_output(data, img)


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
    return ask_user_parameters(params)


def non_local_means_denoising(image, params=None, check_params=True):
    """Apply non local means denoising to an image using specified parameters.
    This version uses the skimage library implementation of this filter.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_nlm = {
        "patch_size": [3, "Size of patches used for denoising."],
        "patch_distance": [7, "Maximal search distance (pixels)."],
        "h": [4.5, "Cut-off distance (in gray levels)."],
    }

    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "non-local means denoising", parameters_nlm
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_nlm.items()}
    else:
        selection = params

    p_imas = []  # processed images
    p_serie = []

    if len(image.shape) == 4:
        for serie in np.moveaxis(image, -1, 0):
            for ima in np.moveaxis(serie, -1, 0):
                # denoise using non local means from skimage.restoration
                d_ima = denoise_nl_means(
                    ima,
                    patch_size=selection["patch_size"],
                    patch_distance=selection["patch_distance"],
                    h=selection["h"],
                    preserve_range=True,
                )
                p_serie.append(d_ima)
            p_imas.append(p_serie)
            p_serie = []
        r_imas = np.moveaxis(np.array(p_imas), [0, 1], [-1, -2])

    elif len(image.shape) == 3:  # Images like MT only have an image per slice
        for ima in np.moveaxis(image, -1, 0):
            # denoise using non local means from skimage.restoration
            d_ima = denoise_nl_means(
                ima,
                patch_size=selection["patch_size"],
                patch_distance=selection["patch_distance"],
                h=selection["h"],
                preserve_range=True,
            )
            p_imas.append(d_ima)
        r_imas = np.moveaxis(np.array(p_imas), 0, -1)

    return r_imas, selection


def show_denoised_output(original_image, denoised_image, ask_user="Denoising"):
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
    ax.flat[1].set_title("Denoised Output")
    ax.flat[2].imshow(rms_diff.T, cmap="gray", interpolation="none")
    ax.flat[2].set_title("Residuals")
    plt.show()

    plt.close(fig1)


def non_local_means_2_denoising(image, params=None, check_params=True):
    """Apply non local means denoising to an image using specified parameters.
    This version uses Dipy's implementation of this filter.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_nlm_2 = {
        "N_sigma": [0, ""],
        "patch_radius": [1, ""],
        "block_radius": [2, ""],
        "rician": [True, ""],
    }

    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "non-local means (2) denoising", parameters_nlm_2
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_nlm_2.items()}
    else:
        selection = params

    sigma = estimate_sigma(image, N=selection["N_sigma"])
    # Denoise using dipy's nlmeans filter
    print("\n    ... applying nlm2 denoising filter")
    return (
        nlmeans(
            image,
            sigma=sigma,
            # mask=mask,
            patch_radius=selection["patch_radius"],
            block_radius=selection["block_radius"],
            rician=selection["rician"],
        ),
        selection,
    )


def ascm_denoising(image, params=None, check_params=True):
    """Apply Adapative Soft Coefficient Matching denoising to an image using
    specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_ascm = {
        "N_sigma": [0, ""],
        "patch_radius_small": [1, ""],
        "patch_radius_large": [2, ""],
        "block_radius": [2, ""],
        "rician": [True, ""],
    }

    if params is None and check_params:
        selection = info_and_ask_denoising_params("ASCM denoising", parameters_ascm)
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_ascm.items()}
    else:
        selection = params

    sigma = estimate_sigma(image, N=selection["N_sigma"])

    den_small = nlmeans(
        image,
        sigma=sigma,
        # mask=mask,
        patch_radius=selection["patch_radius_small"],
        block_radius=selection["block_radius"],
        rician=selection["rician"],
    )

    den_large = nlmeans(
        image,
        sigma=sigma,
        # mask=mask,
        patch_radius=selection["patch_radius_large"],
        block_radius=selection["block_radius"],
        rician=selection["rician"],
    )

    if len(image.shape) == 3:
        return adaptive_soft_matching(image, den_small, den_large, sigma), selection

    denoised_image = []
    for i in range(image.shape[-1]):
        denoised_vol = adaptive_soft_matching(
            image[:, :, :, i],
            den_small[:, :, :, i],
            den_large[:, :, :, i],
            sigma[i],
        )
        denoised_image.append(denoised_vol)

    denoised_image = np.moveaxis(np.array(denoised_image), 0, -1)
    return denoised_image, selection


def local_pca_denoising(image, gtab, params, check_params=True):
    """Apply local PCA denoising to the given image using specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        gtab (numpy.ndarray): B-values and gradient directions associated with the
            input image.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_lpca = {
        "correct_bias": [True, ""],
        "smooth": [3, ""],
        "tau_factor": [2.3, ""],
        "patch_radius": [2, ""],
    }
    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "local PCA denoising", parameters_lpca
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_lpca.items()}
    else:
        selection = params


    sigma = pca_noise_estimate(
        image,
        gtab,
        correct_bias=selection["correct_bias"],
        smooth=selection["smooth"],
    )
    return (
        localpca(
            image,
            sigma,
            tau_factor=selection["tau_factor"],
            patch_radius=selection["patch_radius"],
        ),
        selection,
    )


def mp_pca_denoising(image, params=None, check_params=True):
    """Apply Marcenko-Pastur PCA denoising to an image using specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_mp_pca = {
        "patch_radius": [2, ""],
    }
    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "Marcenko-Pastur PCA denoising", parameters_mp_pca
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_mp_pca.items()}
    else:
        selection = params

    return mppca(image, patch_radius=selection["patch_radius"]), selection


def patch2self_denoising(image, bvals, params, check_params=True):
    """Apply patch2self denoising to the given image using specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        bvals (numpy.ndarray): B-values associated with the input image.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_p2s = {
        "model": ["ols", ""],
        "shift_intensity": [True, ""],
        "clip_negative_vals": [False, ""],
        "b0_threshold": [50, ""],
    }
    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "patch2self denoising", parameters_p2s
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_p2s.items()}
    else:
        selection = params

    return (
        patch2self(
            image,
            bvals,
            model=selection["model"],
            shift_intensity=selection["shift_intensity"],
            clip_negative_vals=selection["clip_negative_vals"],
            b0_threshold=selection["b0_threshold"],
        ),
        selection,
    )


def main():
    denoise()


if __name__ == "__main__":
    main()
