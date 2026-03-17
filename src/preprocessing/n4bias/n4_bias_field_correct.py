import numpy as np
import SimpleITK as sitk  # simpleitk library
from src.utils.utils import show_bias_field_correction_ask, rename_associated_files, info_and_ask_denoising_params


def n4_bias_field_correct(
        nifti_file_path, corrected_nii_output_path=None, params=None, check_params=True
):
    parameters_n4bias = {
        "shrink_factor": [1, "(1 for none)"],
        "number_fitting_levels": [4, ""],
        "number_of_iterations": [50, ""],
        "save_bias_field": [False, ""],
        "use_first_field_only_4d": [True, ""],
    }

    result_ok = False

    while not result_ok:

        if params is None and check_params:
            selection = info_and_ask_denoising_params(
                "N4 bias field correction", parameters_n4bias
            )
        elif params is None and not check_params:
            selection = {key: value[0] for key, value in parameters_n4bias.items()}
        else:
            selection = params

        original_img = sitk.ReadImage(nifti_file_path)

        if len(original_img.GetSize()) == 4:
            original_img_4d = original_img
            original_img = original_img[:, :, :, 0]
        else:
            original_img_4d = False

        otsu_mask = sitk.OtsuThreshold(original_img, 0, 1, 200)

        if selection["shrink_factor"] > 1:
            original_img_shrink = sitk.Shrink(
                original_img, [selection["shrink_factor"]] * original_img.GetDimension()
            )
            otsu_mask_shrink = sitk.Shrink(
                otsu_mask, [selection["shrink_factor"]] * original_img.GetDimension()
            )
        else:
            original_img_shrink = original_img
            otsu_mask_shrink = otsu_mask

        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        corrector.SetMaximumNumberOfIterations(
            [int(selection["number_of_iterations"])]
            * selection["number_fitting_levels"]
        )

        _ = corrector.Execute(original_img_shrink, otsu_mask_shrink)
        log_bias_field = corrector.GetLogBiasFieldAsImage(original_img)
        corrected_image_fullres = original_img / sitk.Exp(log_bias_field)

        if original_img_4d is not False:
            corrected_image_list = []
            if selection["use_first_field_only_4d"]:
                for i in range(original_img_4d.GetSize()[-1]):
                    corrected_image_list.append(
                        original_img_4d[:, :, :, i] / sitk.Exp(log_bias_field)
                    )
                corrected_image_fullres = sitk.JoinSeries(corrected_image_list)
            else:
                log_fields_list = []
                for i in range(original_img_4d.GetSize()[-1]):
                    if selection["shrink_factor"] > 1:
                        img_shrink = sitk.Shrink(
                            original_img_4d[:, :, :, i],
                            [selection["shrink_factor"]] * original_img.GetDimension(),
                        )
                    else:
                        img_shrink = original_img_4d[:, :, :, i]
                    _ = corrector.Execute(img_shrink, otsu_mask_shrink)
                    log_bias_field = corrector.GetLogBiasFieldAsImage(original_img)
                    corrected_image_list.append(
                        original_img_4d[:, :, :, i] / sitk.Exp(log_bias_field)
                    )
                    log_fields_list.append(log_bias_field)
                corrected_image_fullres = sitk.JoinSeries(corrected_image_list)
                log_bias_field = sitk.JoinSeries(log_fields_list)

        if check_params:
            if original_img_4d is False or selection["use_first_field_only_4d"]:
                save, reprocess = show_bias_field_correction_ask(
                    np.swapaxes(sitk.GetArrayFromImage(original_img), 0, 2),
                    np.swapaxes(sitk.GetArrayFromImage(corrected_image_fullres), 0, 2),
                    np.swapaxes(sitk.GetArrayFromImage(log_bias_field), 0, 2),
                )
            else:
                save, reprocess = show_bias_field_correction_ask(
                    np.swapaxes(sitk.GetArrayFromImage(original_img), 0, 2),
                    np.swapaxes(sitk.GetArrayFromImage(corrected_image_fullres), 0, 2),
                    np.swapaxes(
                        sitk.GetArrayFromImage(log_bias_field[:, :, :, 0]), 0, 2
                    ),
                )
            if save or not reprocess:
                result_ok = True
        else:
            save = True
            result_ok = True

    if save:
        if corrected_nii_output_path is None:
            if "_preproc" not in nifti_file_path:
                corrected_nii_output_path = nifti_file_path.replace(
                    ".nii.gz", "_preproc.nii.gz"
                )
                rename_associated_files(corrected_nii_output_path)
            else:
                corrected_nii_output_path = nifti_file_path
        sitk.WriteImage(corrected_image_fullres, corrected_nii_output_path)
        if selection["save_bias_field"]:
            bias_field_nii_path = corrected_nii_output_path.replace(
                ".nii.gz", "_biasf.nii.gz"
            )
            sitk.WriteImage(log_bias_field, bias_field_nii_path)
    else:
        corrected_nii_output_path = nifti_file_path

    return save, corrected_nii_output_path, selection


def main():
    example_file = r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\test_nifti.nii.gz"
    n4_bias_field_correct(example_file)


if __name__ == "__main__":
    main()
