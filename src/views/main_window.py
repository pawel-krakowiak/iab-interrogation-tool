import os
from typing import Dict, List

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
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
from src.models.log_parser import LogParser
from src.models.log_formatter import LogFormatter, ACTION_COLOR_MAP
from src.models.logger_config import logger


class MainWindow(QMainWindow):
    """Main application window for displaying and filtering log entries."""

    def __init__(self) -> None:
        """Initialize the main window, load styles, and set up UI components."""
        super().__init__()
        self.setWindowTitle("Interrogation Log Parser")
        self.setGeometry(200, 200, 1200, 700)
        self.setStyleSheet(self.load_styles())
        self.raw_logs: List[str] = []  # Raw log lines loaded from file.
        self.formatter: LogFormatter = LogFormatter()
        self.sort_order: str = "ASC"  # "ASC" for ascending, "DESC" for descending.
        self.initUI()

    def initUI(self) -> None:
        """Sets up UI elements (left panel, order controls, filter toggles, and workspace)."""
        # --- Left Panel: Logo and File Loader ---
        self.logo_label: QLabel = QLabel(self)
        logo_path: str = os.path.join(os.path.dirname(__file__), "../resources/lssd_logo_bar.png")
        self.logo_label.setPixmap(QPixmap(logo_path).scaled(300, 60, Qt.AspectRatioMode.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label: QLabel = QLabel("Load a log file", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_button: QPushButton = QPushButton("📂 Load Logs", self)
        self.load_button.clicked.connect(self.load_logs)

        left_layout: QVBoxLayout = QVBoxLayout()
        left_layout.addWidget(self.logo_label)
        left_layout.addWidget(self.label)
        left_layout.addWidget(self.load_button)
        left_layout.addStretch()
        left_container: QWidget = QWidget()
        left_container.setLayout(left_layout)
        left_container.setStyleSheet("background-color: #1A2B3C; border-right: 2px solid #FFD700;")

        # --- Right Panel Top: Order Controls ---
        self.order_label: QLabel = QLabel("Logs order", self)
        self.order_label.setFont(QFont("Arial", 12))
        self.order_label.setStyleSheet("color: #FFD700;")
        self.asc_button: QPushButton = QPushButton("ASC ⬆", self)
        self.desc_button: QPushButton = QPushButton("DESC ⬇", self)
        self.asc_button.setCheckable(True)
        self.desc_button.setCheckable(True)
        self.asc_button.setChecked(True)  # Default to ascending.
        self.asc_button.clicked.connect(self.set_order_asc)
        self.desc_button.clicked.connect(self.set_order_desc)
        order_layout: QHBoxLayout = QHBoxLayout()
        order_layout.addWidget(self.order_label)
        order_layout.addWidget(self.asc_button)
        order_layout.addWidget(self.desc_button)
        order_layout.addStretch()

        # --- Right Panel Middle: Toggle Filter Buttons ---
        toggle_names: List[str] = [
            "📅 Tog date",
            "⏰ Tog hour",
            "🙂 Tog /me",
            "🔧 Tog /do",
            "💬 Tog OOC",
            "✉️ Tog PW",
            "⌨️ Tog Commands",
            "❓ Tog Unrecognized",
            "📻 Tog Radio",
        ]
        self.filters: Dict[str, QPushButton] = {}
        filter_panel: QHBoxLayout = QHBoxLayout()
        for name in toggle_names:
            btn: QPushButton = QPushButton(name)
            btn.setCheckable(True)
            btn.setEnabled(False)
            btn.toggled.connect(self.update_workspace)
            self.filters[name] = btn
            filter_panel.addWidget(btn)
        filter_panel.addStretch()

        # Set default toggle states.
        self.filters["📅 Tog date"].setChecked(True)
        self.filters["⏰ Tog hour"].setChecked(True)
        self.filters["🙂 Tog /me"].setChecked(True)
        self.filters["🔧 Tog /do"].setChecked(True)
        self.filters["💬 Tog OOC"].setChecked(True)
        self.filters["✉️ Tog PW"].setChecked(True)
        self.filters["⌨️ Tog Commands"].setChecked(True)
        self.filters["❓ Tog Unrecognized"].setChecked(True)
        self.filters["📻 Tog Radio"].setChecked(True)

        # --- Right Panel Bottom: Workspace ---
        self.workspace: QTextEdit = QTextEdit(self)
        self.workspace.setReadOnly(True)
        self.workspace.setFont(QFont("Courier New", 10))
        self.workspace.setStyleSheet("background-color: #0F1B29; color: #FFD700; border: 1px solid #555;")
        self.workspace.setFrameShape(QFrame.Shape.Box)
        self.workspace.setFrameShadow(QFrame.Shadow.Sunken)
        self.workspace.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        right_layout: QVBoxLayout = QVBoxLayout()
        right_layout.addLayout(order_layout)
        right_layout.addLayout(filter_panel)
        right_layout.addWidget(self.workspace)
        right_container: QWidget = QWidget()
        right_container.setLayout(right_layout)

        # --- Main Layout ---
        main_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(right_container, 3)
        container: QWidget = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def set_order_asc(self) -> None:
        """Set log order to ascending and update workspace."""
        self.sort_order = "ASC"
        self.asc_button.setChecked(True)
        self.desc_button.setChecked(False)
        self.update_workspace()

    def set_order_desc(self) -> None:
        """Set log order to descending and update workspace."""
        self.sort_order = "DESC"
        self.asc_button.setChecked(False)
        self.desc_button.setChecked(True)
        self.update_workspace()

    def load_logs(self) -> None:
        """Loads a log file, stores its lines, enables toggles, and logs the event."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Text Files (*.txt)"
        )
        if file_path:
            logger.info(f"Loaded file: {file_path}")
            parser: LogParser = LogParser(file_path)
            self.raw_logs = parser.logs
            line_count: int = len(self.raw_logs)
            self.label.setText(f"Loaded: {os.path.basename(file_path)} ({line_count} lines)")
            for btn in self.filters.values():
                btn.setEnabled(True)
            self.asc_button.setEnabled(True)
            self.desc_button.setEnabled(True)
            self.update_workspace()

    def update_workspace(self) -> None:
        """
        Updates the workspace display based on current toggle settings and sort order.
        
        The logs are displayed in an HTML table with two columns:
          - The first column shows the row index (for on-screen readability only).
          - The second column shows the formatted log text.
        
        Filtering:
          - 'Tog date' and 'Tog hour' control timestamp parts.
          - 'Tog Radio': if unchecked, radio calls (lines flagged as radio, containing "** [Kanał:" or starting with "Audycja") are excluded.
          - Other toggles filter by log action.
        
        The order of logs is controlled by the ASC/DESC buttons.
        """
        if not self.raw_logs:
            return

        show_date: bool = self.filters["📅 Tog date"].isChecked()
        show_hour: bool = self.filters["⏰ Tog hour"].isChecked()
        filter_me: bool = self.filters["🙂 Tog /me"].isChecked()
        filter_do: bool = self.filters["🔧 Tog /do"].isChecked()
        filter_OOC: bool = self.filters["💬 Tog OOC"].isChecked()
        filter_PW: bool = self.filters["✉️ Tog PW"].isChecked()
        filter_commands: bool = self.filters["⌨️ Tog Commands"].isChecked()
        filter_unrecognized: bool = self.filters["❓ Tog Unrecognized"].isChecked()
        filter_radio: bool = self.filters["📻 Tog Radio"].isChecked()

        # Order logs based on sort_order.
        logs_to_iterate: List[str] = self.raw_logs if self.sort_order == "ASC" else list(reversed(self.raw_logs))
        
        table_rows: List[str] = []
        row_index: int = 1
        for line in logs_to_iterate:
            parsed = self.formatter.parse_line(line)
            if not parsed:
                if filter_unrecognized:
                    row_html = (
                        f"<td style='text-align: right; padding: 2px 5px;'>{row_index}</td>"
                        f"<td><pre style='margin: 0;'>{line}</pre></td>"
                    )
                    table_rows.append(f"<tr>{row_html}</tr>")
                    row_index += 1
                continue

            # Exclude radio calls if Tog Radio is unchecked.
            if not filter_radio:
                if parsed.get("is_radio", False) or "** [Kanał:" in line or parsed["message"].lstrip().startswith("Audycja"):
                    continue

            action: str = parsed["action"]
            if action == "Akcja /me" and not filter_me:
                continue
            if action == "Akcja /do" and not filter_do:
                continue
            if action == "Czat OOC" and not filter_OOC:
                continue
            if action == "PW" and not filter_PW:
                continue
            if action == "Komenda" and not filter_commands:
                continue
            if action not in ACTION_COLOR_MAP and not filter_unrecognized:
                continue

            date_part: str = parsed.get("date", "")
            time_part: str = parsed.get("time", "")
            new_timestamp: str = ""
            if show_date and date_part:
                new_timestamp += date_part
            if show_hour and time_part:
                new_timestamp += (" " if new_timestamp else "") + time_part
            new_timestamp = f"[{new_timestamp}]" if new_timestamp else ""

            timestamp_html: str = f'<span style="color: #00BFFF; font-weight: bold;">{new_timestamp}</span>'
            action_color: str = ACTION_COLOR_MAP.get(action, ACTION_COLOR_MAP["default"])
            action_html: str = f'<span style="color: {action_color}; font-weight: bold;">[{action}]</span>'
            prefix_html: str = ""
            if parsed.get("prefix", ""):
                prefix_html = f'<span style="color: #FFFFFF; font-weight: bold;">{parsed["prefix"]} </span>'
            message_html: str = f'<span style="color: #CCCCCC;">{parsed["message"]}</span>'

            log_line_html: str = " ".join([timestamp_html, action_html, prefix_html, message_html])
            row_html: str = (
                f"<td style='text-align: right; padding: 2px 5px; vertical-align: top;'>{row_index}</td>"
                f"<td style='padding: 2px 5px;'>{log_line_html}</td>"
            )
            table_rows.append(f"<tr>{row_html}</tr>")
            row_index += 1

        table_html: str = "<table style='width: 100%; border-collapse: collapse;'>" + "".join(table_rows) + "</table>"
        self.workspace.setHtml(table_html)

    def load_styles(self) -> str:
        """Returns the application's stylesheet."""
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
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
            QPushButton:checked {
                background-color: #3E5060;
                border: 1px solid #FFD700;
            }
            QPushButton:hover:!disabled {
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
