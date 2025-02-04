from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit


class LogWorkspace(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Workspace")

        self.layout = QVBoxLayout(self)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        self.layout.addWidget(self.text_area)

    def display_logs(self, logs: str) -> None:
        """Wyświetla logi w polu tekstowym."""
        self.text_area.setPlainText(logs)
