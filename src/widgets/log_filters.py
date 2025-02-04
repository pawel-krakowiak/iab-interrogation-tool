from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal


class LogFilters(QWidget):
    filter_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Filters")

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Filter logs by keyword:")
        self.layout.addWidget(self.label)

        self.filter_input = QLineEdit()
        self.layout.addWidget(self.filter_input)

        self.apply_button = QPushButton("Apply Filter")
        self.layout.addWidget(self.apply_button)

        self.apply_button.clicked.connect(self.emit_filter_updated)

    def emit_filter_updated(self) -> None:
        """Wysyła sygnał z nowym filtrem logów."""
        filter_text = self.filter_input.text()
        self.filter_updated.emit(filter_text)
