from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal


class NameSelector(QWidget):
    name_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Name")

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Select Name:")
        self.layout.addWidget(self.label)

        self.combo_box = QComboBox()
        self.layout.addWidget(self.combo_box)

        self.combo_box.currentTextChanged.connect(self.emit_name_selected)

    def set_names(self, names: list[str]) -> None:
        self.combo_box.clear()
        self.combo_box.addItems(names)

    def emit_name_selected(self, name: str) -> None:
        self.name_selected.emit(name)
