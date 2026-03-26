import nibabel as nib

from src.utils.utils import is_valid_nifti


def load_nifti(path: str):
    """
    Load nifti image
    :param path: Path to nifti image
    :return: Numpy array and nifti image
    """
    # Check if file is a valid nifti
    is_valid_nifti(path)

    # Get nifti image from the path
    img = nib.load(path)

    # Get´s image nifti data in numpy array
    data = img.get_fdata()

    return data, img


def get_nifti_slices(data, current_t=0):
    """
    Gets NifTi slices at current time
    :param data: Numpy array with nifti image as data
    :param current_t: Current time index
    :return: Numpy array with sliced nifti image at current time
    """
    slice_max = data.shape[2]
    return [data[:, :, slice_idx, current_t].T for slice_idx in range(slice_max)]
