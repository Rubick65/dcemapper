from pathlib import Path

import nibabel as nib
from dipy.denoise.gibbs import gibbs_removal
from src.utils.utils import show_denoised_output, rename_associated_files
from src.io.nifti_io import load_nifti


def gibbs_remove(processing_filenames_list):
    gibbs_corrected, corrected_filename = gibbs_suppress(
        processing_filenames_list[0]
    )
    if gibbs_corrected:
        if corrected_filename != processing_filenames_list[0]:
            processing_filenames_list[0] = corrected_filename

        for i, nifti_filename in enumerate(
                processing_filenames_list[1:], start=1
        ):
            gibbs_corrected, corrected_filename = gibbs_suppress(
                nifti_filename, check_params=False
            )
            if corrected_filename != nifti_filename:
                processing_filenames_list[i] = corrected_filename


def gibbs_suppress(nifti_file_path, unringed_nii_output_path=None, check_params=True):
    original_img, study_nii = load_nifti(nifti_file_path)
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
                rename_associated_files(unringed_nii_output_path)
            else:
                unringed_nii_output_path = nifti_file_path

        nii_ima = nib.Nifti1Image(unringed_img, study_nii.affine, study_nii.header)
        nib.save(nii_ima, unringed_nii_output_path)

    else:
        unringed_nii_output_path = nifti_file_path

    return keep_unringed, unringed_nii_output_path


def main():
    example_file = [r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\test_nifti.nii.gz"]
    gibbs_remove(example_file)


if __name__ == "__main__":
    main()
