import os
from nibabel.testing import data_path
from src.io.nfti_loader import load_nifti

def main():
    example_file =  os.path.join(data_path, 'example4d.nii.gz')
    load_nifti(example_file)

if __name__ == "__main__":
    main()

