preprocessing_actions_dict = {
    "Gibbs": "&Gibbs artifact suppression",
}

denoise_filters_dict = {
    "&Non local means skimage": "Non local denoising filter",
    "&Non local means skimage dipy's": "Non local denoising filter 2",
    "&Adaptative Soft Coefficient Matching": "Adaptative Soft Coefficient Matching",
}

file_options_dict = {
    "&Open BIDS": "Opens BIDS structure and search for correct file",
    "&Open NIfTI File": "Opens NIfTI files",
    "&Open Bruker File": "Converts from Bruker to NIfTI format",
}
denoise_filters = [
    "Non local means skimage",
    "Non local means skimage dipy's",
    "Adaptative Soft Coefficient Matching"
]

roi_actions_dict = {
    "Rectangle": "ROI selection in form of rectangle",
    "Elliptical": "ROI selection in form of an ellipsis",
    "Polygonal": "ROI selection in form of points selection",
}

shortcuts_dict = {
    "←": "Navigate to previous slice (Z-axis)",
    "→": "Navigate to next slice (Z-axis)",
    "↑": "Navigate to next temporal frame",
    "↓": "Navigate to previous temporal frame",
    "Space": "Toggle playback mode (Movie Mode)",
    "H": "Reset viewport to default orientation (Home)",
    "R": "Restore default container dimensions",
    ",": "Step back to previous zoom level",
    ".": "Step forward to next zoom level",
    "Z": "Toggle interactive Zoom tool",
    "M": "Toggle interactive Pan (Move) tool",
    "F": "Toggle Full Screen mode",
    "Ctrl + Z": "Reset segmentation mask in current slice"
}
