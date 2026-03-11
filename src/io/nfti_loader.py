import os
import numpy as np
import nibabel as nib

def load_nifti(path: str):
    # Load file
    img = nib.load(path)
    data = img.get_fdata()

    print(data.shape)

