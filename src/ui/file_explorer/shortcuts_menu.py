from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QScrollArea, QAbstractItemView

from src.utils.misc import shortcuts_dict


class ShortcutsMenu(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyboard Shortcuts")
        self.setFixedSize(400, 400)

        self.table = QTableWidget(len(shortcuts_dict), 2)
        self.table.setHorizontalHeaderLabels(["Key", "Action"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.create_shortcuts()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.table)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(scroll)
        self.setLayout(self.main_layout)

    def create_shortcuts(self):
        for row, (key, info) in enumerate(shortcuts_dict.items()):
            item_key = QTableWidgetItem(key)
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_info = QTableWidgetItem(info)

            self.table.setItem(row, 0, item_key)
            self.table.setItem(row, 1, item_info)

