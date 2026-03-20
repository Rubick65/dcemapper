import re
from pathlib import Path

from src.utils.utils import is_folder_and_not_occult, is_nii


def get_files_to_process(main_path):
    root_path = Path(main_path)
    source_data_folder = root_path / "sourcedata"
    derivatives_folder = root_path / "derivatives"

    files_to_process = {}

    for study_path in filter(is_folder_and_not_occult, source_data_folder.iterdir()):
        acqs = []
        for sub in filter(is_folder_and_not_occult, study_path.iterdir()):
            if sub.name == "perf":
                file = get_correct_file(sub)
                if file:
                    acqs.append(file)
        if acqs:
            files_to_process[study_path.name] = list(set(acqs))

    if not derivatives_folder.exists():
        derivatives_folder.mkdir()
        return files_to_process

    for derivative_folder in filter(is_folder_and_not_occult, derivatives_folder.iterdir()):
        if derivative_folder in files_to_process:
            del files_to_process[derivative_folder]

    return files_to_process


def get_correct_file(sub):
    for file in filter(is_nii, sub.iterdir()):
        if "_DCE_acq" in file.name:
            return file
    return None


def get_acq(filename):
    """Safely extracts acq tag or returns 'default'."""
    match = re.search(r"acq-([^_]+)", filename)
    return match.group(0) if match else "acq-default"


def main():
    test_path = r"C:\Users\marti\Documents\datos prueba\archivos_raquel\resomapper_output"
    files_to_process = get_files_to_process(test_path)

    for file, archive in files_to_process.items():
        print(f"{file}: {archive}")


if __name__ == '__main__':
    main()
