ACQ_CATEGORIES_BIDS = {
    "localizer": "anat", "T2w": "anat", "T1w": "anat", "T1map_acq": "anat",
    "T2map_acq": "anat", "T2starmap_acq": "anat", "MTon": "anat",
    "MToff": "anat", "fmap": "fmap", "dwi": "dwi", "dce": "perf", "etc": "etc",
}

CONDITIONS_DICT_MRS = {
    "T2w": [lambda p: "fse" in p["seq_name"].lower()],
    "T1w": [lambda p: "se" in p["seq_name"].lower(), lambda p: "t1" in p["seq_name"].lower(),
            lambda p: "map" not in p["seq_name"].lower()],
    "localizer": [lambda p: "scout" in p["seq_name"].lower()],
    "dwi": [lambda p: "epi" in p["seq_name"].lower(), lambda p: "dti" in p["seq_name"].lower()],
    "T2map_acq": [lambda p: "mems" in p["seq_name"].lower()],
    "T2star_acq": [lambda p: "mge" in p["seq_name"].lower()],
    "T1map_acq": [lambda p: "se" in p["seq_name"].lower(), lambda p: "t1" in p["seq_name"].lower(),
                  lambda p: "map" in p["seq_name"].lower()],
    "dce": [lambda p: "dce" in p["seq_name"].lower()],
}

METADATA_REF_DICOM_MRS = {
    "Date": "AcquisitionDate", "Time": "AcquisitionTime", "UserName": "StudyDescription",
    "SubjectID": "PatientName", "SessionID": "AccessionNumber", "Modality": "Modality",
    "Manufacturer": "Manufacturer", "ManufacturersModelName": "ManufacturerModelName",
    "EchoTime": "EchoTime", "RepetitionTime": "RepetitionTime", "FlipAngle": "FlipAngle",
}