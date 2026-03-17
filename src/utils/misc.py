class Logger:
    preprocessing_actions_dict = {
        "Gibbs": "&Gibbs artifact suppression",
        "Bias": "&Bias field correction"
    }

    denoise_filters = [
        "Non local means skimage",
        "Non local means skimage dipy's",
        "Adaptative Soft Coefficient Matching"
    ]

    denoise_filters_dti = [
        "Patch2self denoising",
        "Local PCA denoising",
        "Marcenko-Pastur PCA"
    ]
