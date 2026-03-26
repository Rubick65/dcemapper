import os
import SimpleITK as sitk
from pydicom import dcmread

import warnings

warnings.filterwarnings("ignore")

def convert_dicom_series(dicom_series_path, output_nifti_path):
    """
    Convert dicom files into a unique nifti volume
    :param dicom_series_path:
    :param output_nifti_path:
    :return:
    """
    # Read the series of DICOM files
    reader = sitk.ImageSeriesReader()
    # Obtain the name of the files of the same series that direct
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_series_path)
    if not dicom_names:
        return

    #Extraction of the metadata and tags
    reader.SetFileNames(dicom_names)
    reader.MetaDataDictionaryArrayUpdateOn()
    reader.LoadPrivateTagsOn()
    try:
        #We read the file and create the obj
        image = reader.Execute()

        #Check of extension
        if not output_nifti_path.endswith('.nii.gz'):
            output_nifti_path = output_nifti_path.replace('.nii', '') + '.nii.gz'

        #We save the volume into the disc
        sitk.WriteImage(image, output_nifti_path)
    except Exception as e:
        print(f"Error to convert the series {dicom_series_path}: {e}")

#def convert_dicom_series(dicom_series_path, output_nifti_path):
#    # Read the series of DICOM files
#    reader = sitk.ImageSeriesReader()
#    dicom_names = reader.GetGDCMSeriesFileNames(dicom_series_path)
#    if not dicom_names:
#        return
#
#    reader.SetFileNames(dicom_names)
#    reader.MetaDataDictionaryArrayUpdateOn()
#    reader.LoadPrivateTagsOn()
#    try:
#        image = reader.Execute()
#
#        if not output_nifti_path.endswith('.nii.gz'):
#            output_nifti_path = output_nifti_path.replace('.nii', '') + '.nii.gz'
#
#        sitk.WriteImage(image, output_nifti_path)
#    except Exception as e:
#        print(f"Error to convert the series {dicom_series_path}: {e}")

def convert_dicom_localizer(dicom_series_path, output_nifti_path):
    convert_dicom_series(dicom_series_path, output_nifti_path)


def get_metadata_value(dicom_series_path, tag_name, unique=True):
    """
    Extraction of the specific metadata touring the dicom files in a directory
    :param dicom_series_path: path to the directory
    :param tag_name: tag of the dicom attribute we want to extract
    :param unique: If we want only unique values
    :return: metadata value
    """
    # filter values files
    files = [os.path.join(dicom_series_path, f) for f in os.listdir(dicom_series_path)
             if not f.startswith('.') and f.lower().endswith(('.dcm', '.dicom', ''))]

    if not files: return None

    values = []
    for f in files:
        try:
            #Reed only the header to be more fast
            ds = dcmread(f, stop_before_pixels=True)
            val = getattr(ds, tag_name, None)
            if val is not None:
                values.append(val)
                #If only want unique values and detect inconsistency, we continue
                if unique and len(set(values)) > 1:
                    continue
        except Exception:
            continue

    #If we want unique values
    if unique:
        return sorted(list(set(values)))
    return values

def get_echo_times_from_dicom(dicom_series_path, output_echo_times_path=None):
    """
    Get echo times from dicom and optional save them
    :param dicom_series_path: path to the dicom directory
    :param output_echo_times_path: Optional path to save it as .txt
    """
    unique_echos = get_metadata_value(dicom_series_path, "EchoTime")

    if output_echo_times_path:
        with open(output_echo_times_path, "w") as f:
            f.write(" ".join(map(str, unique_echos)))
    return unique_echos

def get_rep_times_from_dicom(dicom_series_path, output_rep_times_path=None):
    """
    Get repetition times from dicom and optional save them
    :param dicom_series_path: path to the dicom directory
    :param output_rep_times_path: Optional path to save it as .txt
    :return: the unique repetition
    """
    unique_reps = get_metadata_value(dicom_series_path, "RepetitionTime")

    if output_rep_times_path:
        with open(output_rep_times_path, "w") as f:
            f.write(" ".join(map(str, unique_reps)))
    return unique_reps
