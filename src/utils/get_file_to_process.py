from pathlib import Path

from src.utils.utils import is_folder_and_not_occult, is_nii

def get_files_to_process(main_path):
    # Paths to source data and derivatives
    root_path = Path(main_path)
    source_data_folder = root_path / "sourcedata"
    derivatives_folder = root_path / "derivatives"

    # Dict for file to process
    files_to_process = {}

    # If sourcedata does not exist or is not a directory
    if not source_data_folder.exists() or not source_data_folder.is_dir():
        return files_to_process

    # for every study in the folder
    for study_path in filter(is_folder_and_not_occult, source_data_folder.iterdir()):
        acqs = []
        # For every sub-folder in each study
        for sub in filter(is_folder_and_not_occult, study_path.iterdir()):
            # If the name of the folder is perf
            if sub.name == "perf":
                # Get correct file or files
                file = get_correct_file(sub)
                # If the file exists, is not none
                if file:
                    acqs.append(file)
        # If valid archives exist
        if acqs:
            # Add list of valid files to de dict
            files_to_process[study_path.name] = list(set(acqs))

    # If the sourcedata folder exists but still does not contain valid files
    if not files_to_process:
        return {}

    # If derivatives folder dont exists
    if not derivatives_folder.exists():
        # Create derivatives folder
        derivatives_folder.mkdir()
        # Returns all the files to process
        return files_to_process, derivatives_folder

    # For every study
    for derivative_path in filter(is_folder_and_not_occult, derivatives_folder.iterdir()):
        # Gets the folder name
        folder_name = derivative_path.name
        # If folder name exists in the files to process
        if folder_name in files_to_process:
            # Delete those files to process
            del files_to_process[folder_name]

    return files_to_process, derivatives_folder


def get_correct_file(sub):
    # If files are valid niftis
    for file in filter(is_nii, sub.iterdir()):
        # If the file is a dce file
        if "_DCE_acq" in file.name:
            return file
    return None

