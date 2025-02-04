from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QTextEdit, QVBoxLayout, QWidget
from src.models.log_parser import LogParser
from src.models.logger_config import logger

class MainWindow(QMainWindow):
    """Main application window handling UI and user interactions."""

    def __init__(self):
        """Initializes the main window and its components."""
        super().__init__()
        self.setWindowTitle("Log Parser")
        self.setGeometry(200, 200, 800, 600)
        self.initUI()

    def initUI(self):
        """Sets up UI elements and layout."""
        self.label = QLabel("Load a log file", self)
        self.load_button = QPushButton("Load Logs", self)
        self.load_button.clicked.connect(self.load_logs)

        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.load_button)
        layout.addWidget(self.text_area)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_logs(self):
        """Handles log file selection and display."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Log File", "", "Text Files (*.txt)")
        if file_path:
            logger.info(f"Loaded file: {file_path}")
            parser = LogParser(file_path)
            self.label.setText(f"Loaded: {file_path}")
            self.text_area.setPlainText("\n".join(parser.logs))

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
