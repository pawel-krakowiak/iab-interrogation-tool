from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QFileDialog,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFrame,
)
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap
from PyQt6.QtCore import Qt
from src.models.log_formatter import LogFormatter
from src.models.log_parser import LogParser
from src.models.logger_config import logger


class MainWindow(QMainWindow):
    """Main application window handling UI and user interactions."""

    def __init__(self):
        """Initializes the main window and its components."""
        super().__init__()
        self.setWindowTitle("Interrogation Log Parser")
        self.setGeometry(200, 200, 1200, 700)
        self.setStyleSheet(self.load_styles())  # Apply stylesheet
        self.initUI()

    def initUI(self):
        """Sets up UI elements and layout."""

        # LASD Logo
        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(
            QPixmap("resources/lssd_logo_bar.png").scaled(
                300, 60, Qt.AspectRatioMode.KeepAspectRatio
            )
        )
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # File load section
        self.label = QLabel("Załaduj logi (wyeksportuj .txt z panelu gracza)", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_button = QPushButton("Load Logs", self)
        self.load_button.clicked.connect(self.load_logs)

        # Workspace - log viewer
        self.workspace = QTextEdit(self)
        self.workspace.setReadOnly(True)
        self.workspace.setFont(QFont("Courier New", 10))
        self.workspace.setStyleSheet(
            "background-color: #0F1B29; color: #FFD700; border: 1px solid #555;"
        )
        self.workspace.setFrameShape(QFrame.Shape.Box)
        self.workspace.setFrameShadow(QFrame.Shadow.Sunken)
        self.workspace.setLineWrapMode(
            QTextEdit.LineWrapMode.NoWrap
        )  # No text wrapping

        # Left panel layout
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.logo_label)
        left_layout.addWidget(self.label)
        left_layout.addWidget(self.load_button)
        left_layout.addStretch()

        left_container = QWidget()
        left_container.setLayout(left_layout)
        left_container.setStyleSheet(
            "background-color: #1A2B3C; border-right: 2px solid #FFD700;"
        )  # LASD Dark Theme

        # Main horizontal layout (left panel + workspace)
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_container, 1)  # Smaller left panel
        main_layout.addWidget(self.workspace, 3)  # Larger log display area

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_logs(self):
        """Handles log file selection and display."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Text Files (*.txt)"
        )
        if file_path:
            logger.info(f"Loaded file: {file_path}")
            parser = LogParser(file_path)
            formatter = LogFormatter()
            self.label.setText(f"Loaded: {file_path}")

            # Format each log line to HTML
            formatted_lines = []
            for line in parser.logs:
                formatted_line = formatter.format_line(line)
                formatted_lines.append(formatted_line)

            # Join formatted lines and set as HTML content
            html_content = "<br>".join(formatted_lines)
            self.workspace.setHtml(html_content)

    def load_styles(self) -> str:
        """Returns the stylesheet for the application."""
        return """
            QMainWindow {
                background-color: #14202E;
            }
            QLabel {
                color: #FFD700;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2D3E50;
                color: #FFD700;
                border: 1px solid #FFD700;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3E5060;
            }
            QTextEdit {
                background-color: #0F1B29;
                color: #FFD700;
                border: 1px solid #555;
            }
        """


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
