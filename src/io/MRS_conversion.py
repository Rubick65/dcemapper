import json
import os
import warnings
import pydicom
from pydicom import dcmread,valuerep,uid #check
import Dicom_conversion as dcmconv
import MRS_data as md

warnings.filterwarnings("ignore")

def is_folder_valid(path):
    #If folder is a dir and is not occult
    return os.path.isdir(path) and not os.path.basename(path).startswith(".")

def clean_bids_id(s):
    return "".join([c for c in str(s) if c.isalnum()])

def dicom_to_json_serializable(value):
    """
    Converts pydicom-specific data types to JSON-compatible strings/lists
    """
    if isinstance(value, (pydicom.valuerep.PersonName, pydicom.valuerep.DSfloat, pydicom.valuerep.IS, pydicom.uid.UID)):
        return str(value)
    elif isinstance(value, list):
        return [dicom_to_json_serializable(v) for v in value]
    return value

def get_modality_mrs(params):
    for modality, conditions in md.CONDITIONS_DICT_MRS.items():
        if all(cond(params) for cond in conditions):
            return modality
    return "unknown"

def create_metadata_json_MRS(dicom_path, json_output_path, modality):
    """
    DICOM metadata extraction and generation of the .json file required by BIDS
    """
    info_json = {}
    #We read the first DICOM file to get the header
    files = [f for f in os.listdir(dicom_path) if not f.startswith('.')]
    if not files:
        return

    dicom_data = dcmread(os.path.join(dicom_path, files[0]), stop_before_pixels=True)

    for bids_key, dicom_field in md.METADATA_REF_DICOM_MRS.items():
        value = dicom_data.get(dicom_field, None)

        if value is not None:
            val_to_save = value.value if hasattr(value, 'value') else value
            info_json[bids_key] = dicom_to_json_serializable(val_to_save)

    if "T1" in modality:
        reps = dcmconv.get_rep_times_from_dicom(dicom_path)
        if reps: info_json["RepetitionTime"] = reps

    if "T2" in modality:
        echos = dcmconv.get_echo_times_from_dicom(dicom_path)
        if echos: info_json["EchoTime"] = echos

    info_json = {k: v for k, v in info_json.items() if v is not None}

    with open(json_output_path, "w") as f:
        json.dump(info_json, f, indent=4)

def btable_to_bval_bvec(btable_path, output_filename, output_path):
    """
    Convert the MR Solutions btable.txt file to the FSL standard (.bval and .bvec)
    """
    if not os.path.exists(btable_path): return

    with open(btable_path, 'r') as f:
        lines = f.readlines()

    bvals, bvec_x, bvec_y, bvec_z = [], [], [], []
    for line in lines:
        v = line.strip().split('\t')
        if len(v) < 4:
            continue
        bvals.append(v[0])
        bvec_x.append(v[1])
        bvec_y.append(v[2])
        bvec_z.append(v[3])

    with open(os.path.join(output_path, output_filename + ".bval"), 'w') as f:
        f.write(' '.join(bvals) + '\n')
    with open(os.path.join(output_path, output_filename + ".bvec"), 'w') as f:
        f.write(' '.join(bvec_x) + '\n')
        f.write(' '.join(bvec_y) + '\n')
        f.write(' '.join(bvec_z) + '\n')

#Main function
def convert_single_study_mrs(path, output_dir):
    dicom_dir = os.path.join(path, "DICOM")
    sur_dir = os.path.join(path, "Image")
    clean_sub = None

    if not os.path.exists(dicom_dir):
        return None

    for acq_id in os.listdir(dicom_dir):
        acq_path = os.path.join(dicom_dir, acq_id)

        if not is_folder_valid(acq_path):
            continue

        for reco_id in os.listdir(acq_path):
            reco_path = os.path.join(acq_path, reco_id)
            if not is_folder_valid(reco_path) or reco_id != "1":
                continue

            files = [f for f in os.listdir(reco_path)
                     if not f.startswith('.') and f.lower().endswith(('.dcm', '.dicom', ''))]

            if not files:
                continue

            try:
                ds = dcmread(os.path.join(reco_path, files[0]), stop_before_pixels=True)
            except Exception as e:
                continue

            raw_seq_tag = ds.get((0x0018, 0x0024), "")
            seq_name_val = str(raw_seq_tag.value) if hasattr(raw_seq_tag, 'value') else str(raw_seq_tag)

            params = {
                "seq_name": seq_name_val,
                "patient_ID": str(ds.get((0x0010, 0x0020), "unknown")),
                "accs_num": str(ds.get((0x0008, 0x0050), "00")),
                "image_type": str(ds.get((0x0008, 0x0008), "ORIGINAL"))
            }

            if "DERIVED" in params["image_type"].upper():
                continue

            modality = get_modality_mrs(params)
            if modality == "unknown":
                continue

            clean_sub = clean_bids_id(params['patient_ID'])
            clean_ses = clean_bids_id(params['accs_num'])

            subj_sess_prefix = f"sub-{clean_sub}_ses-{clean_ses}"
            category = md.ACQ_CATEGORIES_BIDS.get(modality, "anat")

            final_out_dir = os.path.join(output_dir, f"sub-{clean_sub}", f"ses-{clean_ses}", category)
            os.makedirs(final_out_dir, exist_ok=True)

            acq_filename = f"{subj_sess_prefix}_acq-{acq_id}_run-{reco_id}_{modality}"
            nii_path = os.path.join(final_out_dir, acq_filename + ".nii.gz")
            json_path = os.path.join(final_out_dir, acq_filename + ".json")

            dcmconv.convert_dicom_series(reco_path, nii_path)

            create_metadata_json_MRS(reco_path, json_path, modality)

            if modality == "dwi":
                btable = os.path.join(sur_dir, acq_id, reco_id, "btable.txt")
                if os.path.exists(btable):
                    btable_to_bval_bvec(btable, acq_filename, final_out_dir)
                else:
                    print(f"Aviso: Se detectó DWI pero no se encontró btable en {btable}")

    return clean_sub