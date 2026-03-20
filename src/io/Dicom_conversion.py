import os
import SimpleITK as sitk
from pydicom import dcmread

import warnings

warnings.filterwarnings("ignore")

def convert_dicom_series(dicom_series_path, output_nifti_path):
    # Read the series of DICOM files
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(dicom_series_path)
    if not dicom_names:
        return

    reader.SetFileNames(dicom_names)
    reader.MetaDataDictionaryArrayUpdateOn()
    reader.LoadPrivateTagsOn()
    try:
        image = reader.Execute()

        if not output_nifti_path.endswith('.nii.gz'):
            output_nifti_path = output_nifti_path.replace('.nii', '') + '.nii.gz'

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
    files = [os.path.join(dicom_series_path, f) for f in os.listdir(dicom_series_path)
             if not f.startswith('.') and f.lower().endswith(('.dcm', '.dicom', ''))]

    if not files: return None

    values = []
    for f in files:
        try:
            ds = dcmread(f, stop_before_pixels=True)
            val = getattr(ds, tag_name, None)
            if val is not None:
                values.append(val)
                if unique and len(set(values)) > 1:
                    continue
        except Exception:
            continue

    if unique:
        return sorted(list(set(values)))
    return values

def get_echo_times_from_dicom(dicom_series_path, output_echo_times_path=None):
    unique_echos = get_metadata_value(dicom_series_path, "EchoTime")

    if output_echo_times_path:
        with open(output_echo_times_path, "w") as f:
            f.write(" ".join(map(str, unique_echos)))
    return unique_echos

def get_rep_times_from_dicom(dicom_series_path, output_rep_times_path=None):
    unique_reps = get_metadata_value(dicom_series_path, "RepetitionTime")

    if output_rep_times_path:
        with open(output_rep_times_path, "w") as f:
            f.write(" ".join(map(str, unique_reps)))
    return unique_reps


if __name__ == "__main__":
    input_path = r"C:/Users/hugdp/Desktop/Test_converters/dicom/0002.DCM"
    output_folder = r"C:/Users/hugdp/Desktop/Test_converters/dicom/output"
    output_path = os.path.join(output_folder, "resultado_conversion.nii.gz")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"--- Iniciando procesamiento de: {input_path} ---")

    if os.path.isdir(input_path):
        print("Detectada carpeta, intentando leer como serie...")
        convert_dicom_series(input_path, output_path)

    elif os.path.isfile(input_path):
        print("Detectado archivo único, intentando lectura directa...")
        try:
            img = sitk.ReadImage(input_path)
            sitk.WriteImage(img, output_path)
            print(f"¡Éxito! Archivo convertido en: {output_path}")
        except Exception as e:
            print(f"Error crítico al leer el archivo: {e}")
    else:
        print("La ruta no existe. Revisa si el archivo está descomprimido.")

    print("\n--- Analizando metadatos (MRI tags) ---")
    directorio = os.path.dirname(input_path)

    tiempos_echo = get_echo_times_from_dicom(directorio)
    if tiempos_echo:
        print(f"Tiempos de Eco: {tiempos_echo}")
    else:
        print("EchoTime no disponible")
