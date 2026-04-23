from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import QFileDialog, QMenuBar, QMenu

from src.io.bruker_conversion import convert_studies_from_bruker
from src.ui.file_explorer.shortcuts_menu import ShortcutsMenu
from src.utils.get_file_to_process import get_files_to_process
from src.utils.misc import denoise_filters_dict, file_options_dict, processing_types_dict
from src.utils.utils import get_correct_subject


class NonePersistentMenu(QMenu):
    def leaveEvent(self, a0):
        if self.underMouse():
            return

        active_action = self.activeAction()
        if active_action and active_action.menu() and active_action.menu().isVisible():
            return

        super().hide()


class PersistentMenu(NonePersistentMenu):

    def mouseReleaseEvent(self, event):
        """
        Overrides default mouse release action, new action
        only hides the menu when clicked outside the menu
        :param event:
        :return: None
        """
        # Gets the action at its position
        action = self.actionAt(event.pos())

        # When the action is done in a Persistan Menu option
        if action and action.isCheckable():
            # The normal action is triggered
            action.trigger()
        else:
            # If the click is outside, the menu hides
            super().mouseReleaseEvent(event)


class ProcessedMenu(PersistentMenu):
    process_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process_menu = None
        self.process_action = None
        self.create_processed_types_menu()
        self.triggered.connect(self.check_processing_condition)

    def create_processed_types_menu(self):
        self.setTitle("&Processed")
        self.setMouseTracking(True)
        self.create_processed_menus()

    def create_processed_menus(self):
        self.process_menu = ProcessSelectionMenu()
        self.addMenu(self.process_menu)
        self.process_menu.group.triggered.connect(self.check_processing_condition)
        self.create_processed_action()

    def create_processed_action(self):
        self.process_action = QAction("&Process", self)
        self.process_action.setStatusTip("Start processing")

        self.process_action.setCheckable(False)
        self.process_action.setEnabled(False)
        self.process_action.triggered.connect(self.get_processing_options)

        self.addAction(self.process_action)

    def get_processing_options(self):
        process_options = self.process_menu.group.actions()
        process_selected_option = None
        for option in process_options:

            if option.isChecked():
                process_selected_option = option.text()
                break

        if not process_options:
            return

        self.process_signal.emit(process_selected_option)

    def check_processing_condition(self):
        actions = self.actions()
        activate_process = self.check_processing_actions(actions)

        self.process_action.setEnabled(activate_process)

    def check_processing_actions(self, actions):

        process = False

        for action in actions:
            submenu = action.menu()

            if submenu is not None and isinstance(submenu, QMenu):
                sub_actions = submenu.actions()
                process = self.check_processing_actions(sub_actions)

            else:
                if action.isChecked():
                    process = True
                    break
        return process


class PreprocessingMenu(PersistentMenu):
    preprocess_signal = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gibbs_artifact_suppression = None
        self.denoise_menu = None
        self.preprocessing_action = None
        self.create_preprocessing_menu()
        self.triggered.connect(self.check_preprocessing_condition)

    def create_preprocessing_menu(self):
        """
        Creates preprocessing menu section
        :return: None
        """
        # Create preprocessing menu
        self.setTitle("&Preprocessing")
        # Tracks mouse
        self.setMouseTracking(True)
        self.create_preprocessing_menus()

    def create_preprocessing_menus(self):
        """
        Creates preprocessing actions
        :returns a tuple with all the preprocessing actions
        """
        self.denoise_menu = DenoiseMenu(self)
        self.addMenu(self.denoise_menu)

        # Gibbs artifact suppression
        self.gibbs_artifact_suppression = QAction("&Gibbs artifact suppression", self)
        self.gibbs_artifact_suppression.setStatusTip("Gibbs artifact suppression")
        self.gibbs_artifact_suppression.setCheckable(True)

        self.addAction(self.gibbs_artifact_suppression)
        self.create_preprocessing_action()

    def create_preprocessing_action(self):
        self.preprocessing_action = QAction("&Preprocess", self)
        self.preprocessing_action.setStatusTip("Start preprocessing")

        self.preprocessing_action.setCheckable(False)
        self.preprocessing_action.setEnabled(False)
        self.preprocessing_action.triggered.connect(self.get_preprocessing_options)

        self.addAction(self.preprocessing_action)

    def get_preprocessing_options(self):

        denoise_options = self.denoise_menu.group.actions()
        denoise_selected_option = None
        gibbs = None
        for option in denoise_options:
            if option.isChecked():
                denoise_selected_option = option.text()
                break

        if self.gibbs_artifact_suppression.isChecked():
            gibbs = self.gibbs_artifact_suppression.text()

        if not denoise_options and not gibbs:
            return

        self.preprocess_signal.emit((denoise_selected_option, gibbs))

    def check_preprocessing_condition(self):

        actions = self.actions()
        activate_preprocess = self.check_preprocessing_actions(actions)

        self.preprocessing_action.setEnabled(activate_preprocess)

    def check_preprocessing_actions(self, actions):

        preprocess = False
        for action in actions:
            submenu = action.menu()

            if submenu is not None and isinstance(submenu, QMenu):
                sub_actions = submenu.actions()
                preprocess = self.check_preprocessing_actions(sub_actions)
            else:
                if action.isChecked():
                    preprocess = True
                    break

        return preprocess


class ProcessSelectionMenu(PersistentMenu):
    activate_process_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process_options = []
        self.group = QActionGroup(self)
        self.group.setExclusive(False)
        self.initMenu()

    def initMenu(self):
        self.setTitle("&Type")
        self.processing_actions()
        self.group.triggered.connect(self.handle_exclusivity)

    def processing_actions(self):
        for action, status_tip in processing_types_dict.items():
            proc_option = QAction(action, self)
            proc_option.setStatusTip(status_tip)
            proc_option.setCheckable(True)

            self.group.addAction(proc_option)
            self.addAction(proc_option)

            self.process_options.append(proc_option)

    def handle_exclusivity(self, selected_action):
        if selected_action.isChecked():
            for action in self.group.actions():
                if action is not selected_action:
                    action.setChecked(False)


class DenoiseMenu(PersistentMenu):
    activate_preprocess_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.denoising_filters = []
        self.group = QActionGroup(self)
        self.group.setExclusive(False)
        self.initMenu()

    def initMenu(self):
        self.setTitle("&Denoising")
        self.denoising_filter_actions()
        self.group.triggered.connect(self.handle_exclusivity)

    def denoising_filter_actions(self):
        for action, status_tip in denoise_filters_dict.items():
            denoising_filter = QAction(action, self)
            denoising_filter.setStatusTip(status_tip)
            denoising_filter.setCheckable(True)

            self.group.addAction(denoising_filter)
            self.addAction(denoising_filter)

            self.denoising_filters.append(denoising_filter)

    def handle_exclusivity(self, selected_action):

        if selected_action.isChecked():
            for action in self.group.actions():
                if action is not selected_action:
                    action.setChecked(False)


class MaskMenu(PersistentMenu):
    check_for_roi_changes_signal = pyqtSignal()
    open_selected_mask_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.save_action = QAction("&Save current Mask", self)
        self.open_mask_action = QAction("&Open mask", self)
        self.group = QActionGroup(self)
        self.initUi()

    def initUi(self):
        self.save_roi_action()
        self.open_mask_action_create()

    def save_roi_action(self):
        self.save_action.setStatusTip("Save Mask")
        self.save_action.setEnabled(True)
        self.save_action.triggered.connect(self.check_for_roi_changes_signal.emit)
        self.group.addAction(self.save_action)
        self.addAction(self.save_action)

    def open_mask_action_create(self):
        self.open_mask_action.setStatusTip("Open Mask")
        self.open_mask_action.setEnabled(True)
        self.open_mask_action.triggered.connect(self.open_selected_mask_signal.emit)
        self.group.addAction(self.open_mask_action)
        self.addAction(self.open_mask_action)


class FileMenu(PersistentMenu):
    # Signal for the selected files
    files_signal = pyqtSignal(tuple)

    one_file_signal = pyqtSignal(tuple)

    proc_file_signal = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.save_menu = None
        self.denoising_filters = []
        self.group = QActionGroup(self)
        self.group.setExclusive(False)
        self.file_list = []
        self.current_file_counter = 0
        self.next_action = None
        self.derivative_folder = None
        self.previous_action = None
        self.initMenu()

    def initMenu(self):
        self.setTitle("&File")
        self.file_actions()
        self.group.triggered.connect(self.open_file_action)

    def file_actions(self):
        self.open_file_actions()

        self.displacer_action()

        self.create_save_menu()

    def displacer_action(self):
        self.next_action = QAction("&Next", self)
        self.next_action.setStatusTip("Button for going to next subject studies")
        self.next_action.setEnabled(False)
        self.next_action.triggered.connect(self.next_file)

        self.previous_action = QAction("&Previous", self)
        self.previous_action.setStatusTip("Button for going to previous subject studies")
        self.previous_action.setEnabled(False)
        self.previous_action.triggered.connect(self.previous_file)

        self.addAction(self.previous_action)
        self.addAction(self.next_action)

    def open_file_actions(self):
        open_file_menu = PersistentMenu(self)
        open_file_menu.setTitle("&Open")

        for action, status_tip in file_options_dict.items():
            file_option = QAction(action, self)
            file_option.setStatusTip(status_tip)

            self.group.addAction(file_option)
            open_file_menu.addAction(file_option)

        self.addMenu(open_file_menu)

    def open_file_action(self, selected_action):
        selected_action_text = selected_action.text().split(" ")[1][0:2].lower()

        self.different_file_options(selected_action_text)

    def file_selector(self, directory=True):
        """
        Opens PyQt6 file explorer and emits a signal with the path
        to the selected files
        :return: Path or paths with the selected files
        """
        # Widget for file explorer
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)

        # Indicates the original directory
        dialog.setDirectory(r'C:\Users\Documents')

        if directory:
            # Only shows existing files
            dialog.setFileMode(QFileDialog.FileMode.Directory)
        else:
            dialog.setNameFilter("(*.nii.gz *.nii)")
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        # Filter only for indicated files
        # Detailed mode
        dialog.setViewMode(QFileDialog.ViewMode.Detail)

        # if file explorer widget is executed
        if dialog.exec():
            # Stores selected files
            files = dialog.selectedFiles()
            # If files exists
            if files:
                # Emits a signal with the path to the files
                return files
                # self.file_signal.emit(files)
        else:
            raise ValueError()

    def different_file_options(self, selected_option):
        derivative_folder = None
        self.file_list = []
        self.current_file_counter = 0
        try:
            match selected_option:
                case "bi":
                    path = self.file_selector()
                    files_to_process, derivative_folder = get_files_to_process(path[0])

                    self.get_list_of_files_to_process(files_to_process)

                case "ni":
                    f = self.file_selector(directory=False)

                    derivative_folder = str(Path(f[0]).parent)
                    self.one_file_signal.emit((f[0], derivative_folder))
                    self.next_action.setEnabled(False)
                    self.previous_action.setEnabled(False)

                case "br":
                    path = self.file_selector()
                    input_path = path[0]
                    output_path = Path(input_path).parent

                    convert_studies_from_bruker(input_path, output_path)
                    files_to_process, derivative_folder = get_files_to_process(output_path)

                    self.get_list_of_files_to_process(files_to_process)

                case "pr":
                    f = self.file_selector(directory=False)

                    derivative_folder = str(Path(f[0]).parent)
                    self.proc_file_signal.emit((f[0], derivative_folder))
                    self.next_action.setEnabled(False)
                    self.previous_action.setEnabled(False)

        except ValueError:
            pass

        if self.file_list:
            self.activate_next_action()
            self.derivative_folder = str(derivative_folder)
            self.files_signal.emit((self.file_list[0], self.derivative_folder))

    def get_list_of_files_to_process(self, files_to_process):
        for file, archive in files_to_process.items():
            archive_text = str(archive[0])
            file = get_correct_subject(archive[0])
            self.file_list.append((file, archive_text))

    def activate_next_action(self):
        if len(self.file_list) <= 1:
            return
        self.next_action.setEnabled(True)

    def next_file(self):
        self.current_file_counter += 1

        if self.current_file_counter == len(self.file_list) - 1:
            self.next_action.setEnabled(False)

        self.files_signal.emit((self.file_list[self.current_file_counter], self.derivative_folder))

        if self.current_file_counter >= 0:
            self.previous_action.setEnabled(True)

    def previous_file(self):
        self.current_file_counter -= 1

        if self.current_file_counter == 0:
            self.previous_action.setEnabled(False)

        self.files_signal.emit((self.file_list[self.current_file_counter], self.derivative_folder))

        if self.current_file_counter < len(self.file_list) - 1:
            self.next_action.setEnabled(True)

    def change_current_file(self, new_file):
        if self.file_list:
            self.file_list[self.current_file_counter] = new_file
            print(self.file_list)

    def create_save_menu(self):
        self.save_menu = MaskMenu(self)
        self.save_menu.setTitle("&Mask")
        self.addMenu(self.save_menu)


class TopMenu(QMenuBar):
    visible = True

    def __init__(self):
        super().__init__()
        self.file_menu = FileMenu(self)
        self.shortcuts = None
        self.shortcuts_action = None
        self.preprocessing_menu = PreprocessingMenu(self)
        self.process_menu = ProcessedMenu(self)
        self.create_top_menu()

    def create_top_menu(self):
        # File menu with all the options
        self.addMenu(self.file_menu)

        # menu section
        self.addMenu(self.preprocessing_menu)
        self.addMenu(self.process_menu)

        self.create_shortcuts_action()

    def create_shortcuts_action(self):
        self.shortcuts_action = QAction("&Shortcuts", self)
        self.shortcuts_action.triggered.connect(self.open_shortcuts)
        self.addAction(self.shortcuts_action)

    def deactivate(self):
        self.preprocessing_menu.setEnabled(False)
        self.process_menu.setEnabled(False)

    def activate(self):
        self.preprocessing_menu.setEnabled(True)
        self.process_menu.setEnabled(True)

    def open_shortcuts(self):
        if self.shortcuts is None:
            self.shortcuts = ShortcutsMenu()

        self.shortcuts.show()
        self.shortcuts.raise_()
