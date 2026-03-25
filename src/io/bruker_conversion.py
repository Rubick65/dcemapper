import json
import brkraw
import nibabel as nib
import numpy as np
import zipfile
import warnings
from pathlib import Path
from src.utils import bruker_data as bd

warnings.filterwarnings("ignore")

def get_modality_bruker(params):
    """
    Identify the bruker modality
    :param params: dict with the parameters of sequence
    :return: the modality
    """
    for modality, conditions in bd.conditions_dict_bruker.items():
        # If all the condition functions for that mode are met, it returns
        if all(cond(params) for cond in conditions):
            return modality
    return "unknown"

def save_as_nifti_and_json(pvdset, scan_id, reco_id, output_path, study_info, extra_info):
    """
    Extract the image from the Bruker object, save it as .nii.gz
    and generate the .json file with the BIDS metadata.
    :param pvdset: object charge by brkraw
    :param scan_id: Scan_id
    :param reco_id: Reconstruction ID
    :param output_path: Base path where the files will be saved.
    :param study_info: General study information dict
    :param extra_info: Additional technical information dict
    :return:
    """
    niiobj = pvdset.get_niftiobj(scan_id, reco_id, slope=True)
    nii_file = output_path.with_suffix(".nii.gz")

    #If we get a list of volumes we stack them in a 4th dimension
    if isinstance(niiobj, list):
        ref_nii = niiobj[0]
        data_list = [nii.get_fdata() for nii in niiobj]
        data = np.stack(data_list, axis=-1)

        final_nii = nib.Nifti1Image(data, ref_nii.affine, header=ref_nii.header)
        final_nii.header.set_data_shape(data.shape)
        final_nii.header.set_xyzt_units(xyz='mm', t='sec')
        final_nii.to_filename(str(nii_file))

    else:
        niiobj.to_filename(str(nii_file))

    # Parsing and cleaning metadata according to the BIDS standard
    results_json = pvdset._parse_json(scan_id, reco_id, metadata=bd.metadata_ref_BIDS_bruker)

    clean_metadata = {}
    for k, v in results_json.items():
        ref_val = bd.metadata_ref_BIDS_bruker.get(k)
        if v is not None and v != ref_val:
            clean_metadata[k] = v

    # Converting milliseconds to seconds
    for time_key in ["RepetitionTime", "EchoTime", "InversionTime"]:
        if time_key in clean_metadata:
            val = clean_metadata[time_key]
            if isinstance(val, list):
                clean_metadata[time_key] = [float(v) / 1000.0 for v in val]
            else:
                clean_metadata[time_key] = float(val) / 1000.0

    #Union of all the metadata and saving
    full_metadata = {**study_info, **clean_metadata, **extra_info}

    with open(output_path.with_suffix(".json"), 'w') as f:
        json.dump(full_metadata, f, indent=4)

def get_study_info(pvdset):
    """
    Extracts basic study identification information from the Bruker object
    :param pvdset: Bruker
    :return: Dictionary with 'Date', 'SubjectID' and 'SessionID' cleaned of special characters.
    """
    pv = pvdset.pvobj

    def clean_id(s):
        return "".join([c for c in str(s) if c.isalnum() or c in ("_", "-")])

    return {
        "Date": str(pvdset.get_scan_time()["date"]),
        "SubjectID": clean_id(getattr(pv, 'subj_id', 'unknown')),
        "SessionID": clean_id(getattr(pv, 'session_id', 'unknown')),
    }

def convert_studies_from_bruker(input_dir, output_dir, skip_existing=True):
    """
    Scan a directory for Bruker studies ('subject' folders or ZIP files)
    and systematically convert them to NIfTI format, organized by category
    Create a BIDS-like folder structure: output_dir/sourcedata/sub-XXX_ses-YYY/anat|func|etc/
    :param input_dir: Directory with Bruker studies
    :param output_dir: Directory where NIfTI format will be saved
    :param skip_existing: if true, skip subjects already processed
    """
    input_path = Path(input_dir)
    output_root = Path(output_dir)

    if not input_path.exists():
        print(f"Error: The input path doesn't exist: {input_dir}")
        return

    stats = {"success": 0, "errors": 0, "skipped": 0}
    error_log = []

    # We search for potential studies
    potential_studies = []
    for f in input_path.rglob("*"):
        if f.name == "subject":
            potential_studies.append(f.parent)
        elif f.suffix == ".zip" and zipfile.is_zipfile(f):
            potential_studies.append(f)

    # If there are no potential studies, we stop
    if not potential_studies:
        return

    # For each potential studie
    for study_path in potential_studies:
        try:
            # We load it and get the basic study identification
            pvdset = brkraw.load(str(study_path))
            study_info = get_study_info(pvdset)

            # Normalization of subject ID according to BIDS standard
            subj_val = study_info['SubjectID']
            if not subj_val.startswith("sub-"):
                subj_val = f"sub-{subj_val}"

            if study_info['SessionID'] and study_info['SessionID'] != "unknown":
                subj_sess = f"{subj_val}_ses-{study_info['SessionID']}"
            else:
                subj_sess = subj_val

            target_base = output_root / "sourcedata" / subj_sess

            if skip_existing and target_base.exists():
                stats["skipped"] += 1
                continue

            # Iterate over all available scans and reconstructions
            for scan_id, recos in pvdset._avail.items():
                try:
                    method = pvdset.get_method(scan_id)
                    for reco_id in recos:
                        visu = pvdset.get_visu_pars(scan_id, reco_id)

                        # Omit derived maps (ISAs) which are usually parametric/intermediate calculations
                        if visu.parameters.get("VisuSeriesTypeId") == "DERIVED_ISA":
                            continue

                        acqp = pvdset.get_acqp(scan_id)
                        rg = acqp.parameters.get("RG", None)

                        try:
                            reco_obj = pvdset.pvobj.get_reco(scan_id, reco_id)
                            reco_slope = reco_obj.parameters.get("RECO_map_slope", None)
                        except:
                            reco_slope = None

                        extra_info = {"ReceiverGain": rg, "RecoSlope": reco_slope}

                        # Gather parameters to identify the modality
                        params = {
                            "scan_method": method.parameters.get("Method"),
                            "mt_on_off": method.parameters.get("PVM_MagTransOnOff", "Off"),
                            "echo_time": visu.parameters.get("VisuAcqEchoTime"),
                            "seq_name": visu.parameters.get("VisuAcquisitionProtocol", ""),
                        }

                        modality = get_modality_bruker(params)

                        if modality == "unknown":
                            msg = f"Skipping Scan {scan_id}: Modality not recognized (Method: {params['scan_method']})"
                            error_log.append(msg)
                            continue

                        # Define destination folder and create it
                        category = bd.acq_categories_BIDS.get(modality, "etc")

                        target_folder = target_base / category
                        target_folder.mkdir(parents=True, exist_ok=True)

                        base_name = f"{subj_sess}_acq-{scan_id}_run-{reco_id}_{modality}"
                        output_full_path = target_folder / base_name

                        #Save the files as nifti and json
                        save_as_nifti_and_json(pvdset, scan_id, reco_id, output_full_path, study_info, extra_info)

                        # If it's DWI, also extract the .bvec and .bval files
                        if modality == "dwi":
                            pvdset.save_bdata(scan_id, base_name, dir=str(target_folder))

                except Exception as e:
                    msg = f"Error in {subj_sess} Scan {scan_id}: {e}"
                    print(f" {msg}")
                    error_log.append(msg)

            stats["success"] += 1

        except Exception as e:
            msg = f"Error while loading {study_path}: {e}"
            print(f" {msg}")
            error_log.append(msg)
            stats["errors"] += 1

    if error_log:
        log_file = output_root / "conversion_report.log"
        with open(log_file, "w") as f:
            f.write("\n".join(error_log))
        print(f"Error details save in: {log_file}")

if __name__ == "__main__":
    input_path = r"C:\Users\marti\Documents\datos prueba\prueba_bruker\20260306_125921_B060326_WTF1_d10_DCE_1_1"
    output_path = r"C:\Users\marti\Documents\datos prueba\prueba_bruker"
    skip_existing = True  # False if we want to overwrite

    print("-" * 50)
    print("Starting the Bruker to Nifti transformation")
    print(f"Input: {Path(input_path).absolute()}")
    print(f"Output:  {Path(output_path).absolute()}")
    print("-" * 50)

    convert_studies_from_bruker(
        input_dir=input_path,
        output_dir=output_path,
        skip_existing=skip_existing
    )

    print("\n" + "=" * 50)
    print("PROCESS FINISHED")
    print(f"CHECK THE FOLDER: {output_path}/sourcedata")

    log_path = Path(output_path) / "conversion_report.log"
    if log_path.exists():
        print(f"ERROR DETECTED, CHECK: {log_path}")
    else:
        print("EVERYTHING WENT WELL")
    print("=" * 50)