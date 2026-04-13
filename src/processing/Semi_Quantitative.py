import os

import matplotlib.pyplot as plt
import numpy as np
import nibabel as nib

from src.io.nifti_io import load_nifti


def semi_quantitative(data, img, semi_quantitative_data: tuple, folders: tuple):
    frame_ini_contrast = semi_quantitative_data[0]
    frame_period = semi_quantitative_data[1]
    output_folder = folders[0]
    nifti_file_path = folders[1]

    reference_value = calculate_reference_value(data, frame_ini_contrast)

    rce = calculate_rce(data, reference_value)

    s, t = data.shape[2] // 2, data.shape[3] // 2

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    ax1.imshow(data[:, :, s, t].T, cmap='gray')
    ax1.set_title(f"ORIGINAL (Max: {np.max(data):.2f})")

    ax2.imshow(rce[:, :, s, t].T, cmap='gray')
    ax2.set_title(f"RCE (Max: {np.max(rce):.2f} %)")

    diff = np.abs(data[:, :, s, t] - rce[:, :, s, t])
    ax3.imshow(diff.T, cmap='magma')
    ax3.set_title("DIFERENCIA (Debe verse algo aquí)")

    plt.show()

    plt.show()
    save_nifit(rce, img.affine, output_folder, nifti_file_path)


def calculate_reference_value(data, n_pixeles):
    primer_frame = data[:, :, :, 0]
    pixeles_con_chicha = primer_frame[primer_frame > 10]

    seleccion = pixeles_con_chicha[:n_pixeles]

    return np.mean(seleccion)


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

    semi_quantitative(data, img, (10, 12, 8),
                      (r"C:\Users\laboratorio\PycharmProjects\dcemapper\src",
                       r"C:\Users\laboratorio\PycharmProjects\dcemapper\src\sub-B060326_WTF1_d10_DCE_acq-10_run-1_dce.nii.gz"))


if __name__ == "__main__":
    main()
