import os
from nibabel.testing import data_path
from src.io.nifti_io import load_nifti


def main():
    example_file = os.path.join(data_path, 'example4d.nii.gz')
    data, img = load_nifti(example_file)

if __name__ == "__main__":
    main()
