preprocessing_actions_dict = {
    "Gibbs": "&Gibbs artifact suppression",
    "Bias": "&Bias field correction"
}

denoise_filters_dict = {
    "&Non local means skimage": "Non local denoising filter",
    "&Non local means skimage dipy's": "Non local denoising filter 2",
    "&Adaptative Soft Coefficient Matching": "Adaptative Soft Coefficient Matching",
}
denoise_filters = [
    "&Non local means skimage",
    "&Non local means skimage dipy's",
    "&Adaptative Soft Coefficient Matching"
]

denoise_filters_dti = [
    "Patch2self denoising",
    "Local PCA denoising",
    "Marcenko-Pastur PCA"
]

roi_actions_dict = {
    "Rectangle ROI": "ROI selection in form of rectangle",
    "Elliptical": "ROI selection in form of an ellipsis"
}
