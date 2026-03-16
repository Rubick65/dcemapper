from dipy.denoise.gibbs import gibbs_removal

import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import SimpleITK as sitk


# TODO: if we remove one of the nlmeans maybe this to remove one dependency

def gibbs_suppress(nifti_file_path, unringed_nii_output_path=None, check_params=True):
    study_nii = nib.load(nifti_file_path)
    original_img = study_nii.get_fdata()
    unringed_img = gibbs_removal(original_img, inplace=False)
    if check_params:
        keep_unringed, _ = show_denoised_output(
            original_img, unringed_img, ask_user="Gibbs"
        )
    else:
        keep_unringed = True

    if keep_unringed:
        if unringed_nii_output_path is None:
            if "_preproc" not in nifti_file_path:
                unringed_nii_output_path = nifti_file_path.replace(
                    ".nii.gz", "_preproc.nii.gz"
                )
                ut.rename_associated_files(unringed_nii_output_path)
            else:
                unringed_nii_output_path = nifti_file_path

        nii_ima = nib.Nifti1Image(unringed_img, study_nii.affine, study_nii.header)
        nib.save(nii_ima, unringed_nii_output_path)

    else:
        unringed_nii_output_path = nifti_file_path

    return keep_unringed, unringed_nii_output_path
