acq_categories_BIDS = {
    "localizer": "anat",
    "T2w": "anat",
    "T1w": "anat",
    "T1map_acq": "anat",
    "T2map_acq": "anat",
    "T2starmap_acq": "anat",
    "MTon": "anat",
    "MToff": "anat",
    "fmap": "fmap",
    "dwi": "dwi",
    "dce": "perf",
    "etc": "etc",
}

conditions_dict_bruker = {
    "T2w": [lambda params: params["scan_method"] == "Bruker:RARE"],
    "T1w": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: "T1" in params["seq_name"],
    ],
    "localizer": [
        lambda params: params["scan_method"] == "Bruker:FLASH"
        and "localiz" in params["seq_name"].lower()
    ],
    "dwi": [lambda params: params["scan_method"] == "Bruker:DtiEpi"],
    "T2map_acq": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: params["mt_on_off"] == "Off",
        lambda params: isinstance(params["echo_time"], list),
    ],
    "T2starmap_acq": [lambda params: params["scan_method"] == "Bruker:MGE"],
    "T1map_acq": [lambda params: params["scan_method"] == "Bruker:RAREVTR"],
    "MTon": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: params["mt_on_off"] == "On",
    ],
    "MToff": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: params["mt_on_off"] == "Off",
        lambda params: not isinstance(params["echo_time"], list),
    ],
    "fmap": [lambda params: params["scan_method"] == "Bruker:FieldMap"],
    "dce": [
        lambda params: params["scan_method"] == "Bruker:FLASH"
        and "dce" in params["seq_name"].lower()
    ],
}

metadata_ref_BIDS_bruker = {
    "Manufacturer": "VisuManufacturer",
    "ManufacturersModelName": "VisuStation",
    "DeviceSerialNumber": "VisuSystemOrderNumber",
    "StationName": "VisuStation",
    "SoftwareVersion": "VisuAcqSoftwareVersion",
    "MagneticFieldStrength": {
        "Equation": "Freq / 42.576",
        "Freq": "VisuAcqImagingFrequency",
    },
    "MatrixCoilMode": "ACQ_experiment_mode",
    "InstitutionName": "VisuInstitution",
    "PulseSequenceDetails": "ACQ_scan_name",
    "PulseSequenceType": "PULPROG",
    "ScanningSequence": "VisuAcqSequenceName",
    "SequenceName": ["VisuAcquisitionProtocol", "ACQ_protocol_name"],
    "SequenceVariant": "VisuAcqEchoSequenceType",
    "ScanOptions": {
        "CG": "VisuCardiacSynchUsed",
        "FC": "VisuAcqFlowCompensation",
        "FP": "VisuAcqSpectralSuppression",
        "PFF": {"idx": 0, "key": "VisuAcqPartialFourier"},
        "PFP": {"idx": 1, "key": "VisuAcqPartialFourier"},
        "RG": "VisuRespSynchUsed",
        "SP": "PVM_FovSatOnOff",
    },
    "NonlinearGradientCorrection": "VisuAcqKSpaceTraversal",
    "EffectiveEchoSpacing": {
        "ACCfactor": "ACQ_phase_factor",
        "BWhzPixel": "VisuAcqPixelBandwidth",
        "Equation": "(1 / (MatSizePE * BWhzPixel)) / " "ACCfactor",
        "MatSizePE": {
            "idx": [
                {"key": "VisuAcqGradEncoding", "where": "phase_enc"},
                {"key": "VisuAcqImagePhaseEncDir", "where": "col_dir"},
            ],
            "key": "VisuCoreSize",
        },
    },
    "NumberShots": "VisuAcqKSpaceTrajectoryCnt",
    "ParallelReductionFactorInPlane": "ACQ_phase_factor",
    "PartialFourier": "VisuAcqPartialFourier",
    "PhaseEncodingDirection": [
        {"key": "VisuAcqGradEncoding", "where": "phase_enc"},
        {"key": "VisuAcqImagePhaseEncDir", "where": "col_dir"},
    ],
    "TotalReadoutTime": {
        "ACCfactor": "ACQ_phase_factor",
        "BWhzPixel": "VisuAcqPixelBandwidth",
        "ETL": "VisuAcqEchoTrainLength",
        "Equation": "(1 / BWhzPixel) / ACCfactor",
    },
    "DwellTime": {"BWhzPixel": "VisuAcqPixelBandwidth", "Equation": "1/BWhzPixel"},
    "EchoTime": "VisuAcqEchoTime",
    "RepetitionTime": "VisuAcqRepetitionTime",
    "InversionTime": "VisuAcqInversionTime",
    "SliceEncodingDirection": [
        {"key": "VisuAcqGradEncoding", "where": "slice_enc"},
        {"EncSeq": "VisuAcqGradEncoding", "Equation": "len(EncSeq)"},
    ],
    "SliceTiming": {
        "Equation": "np.linspace(0, TR/1000, Num_of_Slice + 1)[Order]",
        "Num_of_Slice": "VisuCoreFrameCount",
        "Order": "ACQ_obj_order",
        "TR": "VisuAcqRepetitionTime",
    },
    "FlipAngle": "VisuAcqFlipAngle",
}