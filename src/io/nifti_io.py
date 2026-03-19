import nibabel as nib
import numpy as np

from src.utils.utils import is_valid_nifti

def save_nifti(data, affine, header):
    nifti_img = nib.Nifti1Image(data, affine, header)
    nib.save(nifti_img, "test_nifti.nii.gz")

def load_nifti(path: str):
    is_valid_nifti(path)

    # Get nifti image from the path
    img = nib.load(path)

    # Get´s image nifti data in numpy array
    data = img.get_fdata()
    print(data)

    return data, img


def get_nifti_slices(data):
    slice_max = data.shape[2]
    return [data[:, :, slice_idx, 0].T for slice_idx in range(slice_max)]

    # def show_nifti_info(img, data):
    header = img.header

    print(data.shape)
    print(f"Min intesity: {np.min(data)}")
    print(f"Max intesity: {np.max(data)}")
    print(f"Mean: {np.mean(data)}")

    print(header)
