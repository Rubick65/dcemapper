from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import QStyle, QMenu, QToolButton
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from src.ui.Images_Class.NiftiCanvas import NiftiCanvas
from src.utils.misc import roi_actions_dict, process_view_dict


class RoiMenu(QMenu):
    selected_text_signal = pyqtSignal(str)
    deactivate_roi_selection_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.group = QActionGroup(self)
        self.group.setExclusive(False)
        self.group.triggered.connect(self.handle_exclusivity)
        self.save_action = QAction("&Save ROI", self)
        self.already_processed_roi = False
        self.roi_selection_actions()

    def roi_selection_actions(self):
        # Different roi selection options
        for roi, tip in roi_actions_dict.items():
            roi_option = QAction(roi, self)
            roi_option.setStatusTip(tip)
            roi_option.setCheckable(True)
            roi_option.setEnabled(False)

            self.group.addAction(roi_option)
            self.addAction(roi_option)

    def handle_exclusivity(self, selected_action: QAction):
        if not selected_action.isChecked():
            self.deactivate_roi_selection_signal.emit()
            return

        for action in self.group.actions():
            if action is not selected_action:
                action.setChecked(False)

        self.selected_text_signal.emit(selected_action.text()[0: 1].lower())

    def activate_roi_by_prefix(self, letter):
        for action in self.group.actions():
            if action.text().lower().startswith(letter.lower()):
                action.trigger()
                break

    def activate_roi_selection(self):
        actions = self.group.actions()
        if not actions:
            actions = self.actions()

        for action in actions:
            action.setEnabled(True)

        self.already_processed_roi = True
        self.update()

    def deactivate_roi_selection(self):
        actions = self.group.actions()

        if not actions:
            actions = self.actions()

        for action in actions:
            action.setEnabled(False)

        self.update()


class ViewerMenu(QMenu):
    deactive_viewer_selection_signal = pyqtSignal()
    selected_text_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.group = QActionGroup(self)
        self.group.setExclusive(False)
        self.group.triggered.connect(self.handle_exclusivity)
        self.save_action = QAction("&Change view", self)
        self.already_processed = False
        self.viewer_selection_actions()

    def viewer_selection_actions(self):
        # Different roi selection options
        for viewer, tip in process_view_dict.items():
            viewer_option = QAction(viewer, self)
            viewer_option.setStatusTip(tip)
            viewer_option.setCheckable(True)
            viewer_option.setEnabled(False)

            self.group.addAction(viewer_option)
            self.addAction(viewer_option)

    def activate_viewer_selection(self):
        actions = self.group.actions()
        if not actions:
            actions = self.actions()

        for action in actions:
            action.setEnabled(True)

        self.already_processed = True
        self.update()

    def handle_exclusivity(self, selected_action: QAction):
        if not selected_action.isChecked():
            self.deactive_viewer_selection_signal.emit()
            return

        for action in self.group.actions():
            if action is not selected_action:
                action.setChecked(False)

        self.selected_text_signal.emit(selected_action.text()[0: 1].lower())


class NiftiToolbar(NavigationToolbar):
    previous_roi_signal = pyqtSignal()

    def __init__(self, canvas: NiftiCanvas, parent):
        super().__init__(canvas, parent)
        # We readjust the functions of the arrows to change between slices
        self._actions['back'].triggered.disconnect()
        self._actions['back'].triggered.connect(self.go_back)

        self._actions['forward'].triggered.disconnect()
        self._actions['forward'].triggered.connect(self.go_forward)

        self.destroyed.connect(self._cleanup_canvas)

        # Alert to identify if the current z has changed
        self.canvas.z_changed.connect(self.set_history_buttons)

        self.current_process_view = None

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.add_previous_roi_action()

        self.roi_menu = RoiMenu()
        self.roi_button = QToolButton(self)
        self.add_roi_menu()

        self.viewer_menu = ViewerMenu()
        self.viewer_button = QToolButton(self)
        self.add_viewer_menu()

        self.set_history_buttons()

    def _cleanup_canvas(self):
        if self.canvas:
            self.canvas.close_figure()

    def set_history_buttons(self):
        """
        Check to enable or disable the buttons for moving between slices
        """
        # We check if the current slide is in the limits
        can_backward = self.canvas.current_z > 0
        can_forward = self.canvas.current_z < self.canvas.max_z

        # Depending on the check the button will be enabled or not
        if 'back' in self._actions:
            self._actions['back'].setEnabled(can_backward)
        if 'forward' in self._actions:
            self._actions['forward'].setEnabled(can_forward)

    def go_back(self):
        new_z = max(0, self.canvas.current_z - 1)
        self.canvas.set_z(new_z)
        self.set_history_buttons()

    def go_forward(self):
        new_z = min(self.canvas.max_z, self.canvas.current_z + 1)
        self.canvas.set_z(new_z)
        self.set_history_buttons()

    def add_roi_menu(self):
        self.roi_button.setMenu(self.roi_menu)
        self.roi_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        self.roi_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown)
        self.roi_button.setIcon(icon)

        self.addWidget(self.roi_button)

    def add_previous_roi_action(self):
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)

        previous_roi_action = QAction(icon, "Previous ROI", self)

        previous_roi_action.triggered.connect(self.previous_roi_signal.emit)

        self.addAction(previous_roi_action)

    def add_viewer_menu(self):
        self.viewer_button.setMenu(self.viewer_menu)
        self.viewer_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        self.viewer_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)
        self.viewer_button.setIcon(icon)

        self.addWidget(self.viewer_button)
