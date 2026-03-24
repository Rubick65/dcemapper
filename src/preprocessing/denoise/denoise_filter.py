import os

import nibabel as nib
import numpy as np
from dipy.core.gradients import gradient_table
from dipy.denoise.adaptive_soft_matching import adaptive_soft_matching
from dipy.denoise.localpca import mppca, localpca
from dipy.denoise.nlmeans import nlmeans
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.patch2self import patch2self
from dipy.denoise.pca_noise_estimate import pca_noise_estimate
# TODO: if we remove one of the nlmeans maybe this to remove one dependency
from skimage.restoration import denoise_nl_means

from src.io.nifti_io import load_nifti
from src.utils.utils import create_general_preprocess_output, rename_associated_files, info_and_ask_denoising_params


def denoise_init_one_file(nifti_filename, study_acq_derivatives_dir, selected_filter):
    params, denoised_nii_output_path, selected_filter = denoise(
        nifti_filename,
        study_acq_derivatives_dir,
        params=None,
        selected_filter=selected_filter,
    )
    processing_filename = denoised_nii_output_path

    return processing_filename


def denoise_init(nifti_filename_list, study_acq_derivatives_dir, processing_filenames_list, selected_filter):
    params, denoised_nii_output_path, selected_filter = denoise(
        nifti_filename_list[0],
        study_acq_derivatives_dir,
        params=None,
        selected_filter=selected_filter,
    )
    processing_filenames_list[0] = denoised_nii_output_path

    if (
            len(nifti_filename_list) > 1
            and "_preproc" in processing_filenames_list[0]
    ):
        for i, nifti_filename in enumerate(
                nifti_filename_list[1:], start=1
        ):
            params, denoised_nii_output_path, selected_filter = (
                denoise(
                    nifti_filename,
                    study_acq_derivatives_dir,
                    params=params,
                    selected_filter=selected_filter,
                )
            )
            processing_filenames_list[i] = denoised_nii_output_path

        return processing_filenames_list


def denoise(
        nifti_file_path, output_folder, params=None, selected_filter=None
):
    if params is None:
        check_params = True
    elif params == "default":
        params = None
        check_params = False
    else:
        check_params = False

    process_again = True

    while process_again:
        params = None
        original_image, study_nii = load_nifti(nifti_file_path)

        denoised_image, params = denoise_options(original_image, params, check_params, nifti_file_path, selected_filter)

        if check_params:
            process_again = create_general_preprocess_output(original_image, denoised_image, "Denoised")
        else:
            process_again = False

        if not process_again:

            nii_ima = nib.Nifti1Image(
                denoised_image, study_nii.affine, study_nii.header
            )
            denoised_nii_name = os.path.basename(nifti_file_path).replace(
                ".nii.gz", "_preproc.nii.gz"
            )
            denoised_nii_output_path = os.path.join(
                output_folder, denoised_nii_name
            )
            nib.save(nii_ima, denoised_nii_output_path)
            rename_associated_files(denoised_nii_output_path)
        else:
            denoised_nii_output_path = nifti_file_path

    return params, denoised_nii_output_path, selected_filter


def denoise_options(original_image, params, check_params, nifti_file_path, selected_filter):
    selected_filter = get_selected_filter(selected_filter)
    match selected_filter:
        case "n":
            denoised_image, params = non_local_means_denoising(
                original_image, params, check_params=check_params
            )
        case "d":
            denoised_image, params = non_local_means_2_denoising(
                original_image, params, check_params=check_params
            )
        case "a":
            denoised_image, params = ascm_denoising(
                original_image, params, check_params=check_params
            )
        case "p":
            bval_fname = nifti_file_path.replace(".nii.gz", ".bval")
            bvals = np.loadtxt(bval_fname)
            denoised_image, params = patch2self_denoising(
                original_image, bvals, params, check_params=check_params
            )
        case "l":
            bval_fname = nifti_file_path.replace(".nii.gz", ".bval")
            bvec_fname = nifti_file_path.replace(".nii.gz", ".bvec")
            bvals = np.loadtxt(bval_fname)
            bvecs = np.loadtxt(bvec_fname)
            gtab = gradient_table(bvals, bvecs)
            denoised_image, params = local_pca_denoising(
                original_image, gtab, params, check_params=check_params
            )
        case "m":
            denoised_image, params = mp_pca_denoising(
                original_image, params, check_params=check_params
            )
    return denoised_image, params


def get_selected_filter(selected_filter):
    if "dipy" in selected_filter:
        return "d"

    return selected_filter[1:2].lower()


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
    example_file = [r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\test_nifti.nii.gz"]
    output_file = r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\viewer"
    empty_list = []
    denoise_init(example_file, output_file, empty_list)


if __name__ == "__main__":
    main()
