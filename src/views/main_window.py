import os
from typing import Dict, List, Tuple

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
    QGroupBox,
    QCheckBox,
    QFrame,
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt

from src.models.log_parser import LogParser
from src.models.log_formatter import LogFormatter, ACTION_COLOR_MAP
from src.models.logger_config import logger


class MainWindow(QMainWindow):
    """Main application window for log viewing and filtering, including selection of Interviewer and Interrogated."""

    def __init__(self) -> None:
        """Initialize main window, load styles, and set up UI components."""
        super().__init__()
        self.setWindowTitle("Interrogation Log Parser")
        self.setGeometry(200, 200, 1200, 700)
        self.setStyleSheet(self.load_styles())
        self.raw_logs: List[str] = []  # Raw log lines loaded from file.
        self.formatter: LogFormatter = LogFormatter()
        self.sort_order: str = "ASC"  # "ASC" for ascending, "DESC" for descending.
        # Słowniki dla checkboxów Interviewer/Interrogated:
        self.interviewer_checkboxes: Dict[str, QCheckBox] = {}
        self.interrogated_checkboxes: Dict[str, QCheckBox] = {}
        self.initUI()

    def initUI(self) -> None:
        """Sets up UI elements: lewy panel (logo, load, wybór osób, checkbox 'Show only related'),
        prawy panel (order controls, toggle filtry, workspace)."""
        # ----- Lewy Panel -----
        # Logo i przycisk ładowania
        self.logo_label: QLabel = QLabel(self)
        logo_path: str = os.path.join(
            os.path.dirname(__file__), "../resources/lssd_logo_bar.png"
        )
        self.logo_label.setPixmap(
            QPixmap(logo_path).scaled(300, 60, Qt.AspectRatioMode.KeepAspectRatio)
        )
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label: QLabel = QLabel("Load a log file", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_button: QPushButton = QPushButton("📂 Load Logs", self)
        self.load_button.clicked.connect(self.load_logs)

        # Grupa wyboru Interviewer
        self.interviewer_group: QGroupBox = QGroupBox("Interviewer [I]", self)
        self.interviewer_layout: QVBoxLayout = QVBoxLayout()
        self.interviewer_group.setLayout(self.interviewer_layout)

        # Grupa wyboru Interrogated
        self.interrogated_group: QGroupBox = QGroupBox("Interrogated [O]", self)
        self.interrogated_layout: QVBoxLayout = QVBoxLayout()
        self.interrogated_group.setLayout(self.interrogated_layout)

        # Checkbox "Show only related"
        self.show_only_related_checkbox: QCheckBox = QCheckBox(
            "Show only related", self
        )
        self.show_only_related_checkbox.stateChanged.connect(self.update_workspace)

        left_layout: QVBoxLayout = QVBoxLayout()
        left_layout.addWidget(self.logo_label)
        left_layout.addWidget(self.label)
        left_layout.addWidget(self.load_button)
        left_layout.addWidget(self.interviewer_group)
        left_layout.addWidget(self.interrogated_group)
        left_layout.addWidget(self.show_only_related_checkbox)
        left_layout.addStretch()
        left_container: QWidget = QWidget()
        left_container.setLayout(left_layout)
        left_container.setStyleSheet(
            "background-color: #1A2B3C; border-right: 2px solid #FFD700;"
        )

        # ----- Prawy Panel -----
        # Order Controls
        self.order_label: QLabel = QLabel("Logs order", self)
        self.order_label.setFont(QFont("Arial", 12))
        self.order_label.setStyleSheet("color: #FFD700;")
        self.asc_button: QPushButton = QPushButton("ASC ⬆", self)
        self.desc_button: QPushButton = QPushButton("DESC ⬇", self)
        self.asc_button.setCheckable(True)
        self.desc_button.setCheckable(True)
        self.asc_button.setChecked(True)
        self.asc_button.clicked.connect(self.set_order_asc)
        self.desc_button.clicked.connect(self.set_order_desc)
        order_layout: QHBoxLayout = QHBoxLayout()
        order_layout.addWidget(self.order_label)
        order_layout.addWidget(self.asc_button)
        order_layout.addWidget(self.desc_button)
        order_layout.addStretch()

        # Toggle Filter Buttons (wcześniejsze filtry, np. "Tog date", "Tog /me", "Tog Radio" itd.)
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
        # Ustawienia domyślne.
        self.filters["📅 Tog date"].setChecked(True)
        self.filters["⏰ Tog hour"].setChecked(True)
        self.filters["🙂 Tog /me"].setChecked(True)
        self.filters["🔧 Tog /do"].setChecked(True)
        self.filters["💬 Tog OOC"].setChecked(True)
        self.filters["✉️ Tog PW"].setChecked(True)
        self.filters["⌨️ Tog Commands"].setChecked(True)
        self.filters["❓ Tog Unrecognized"].setChecked(True)
        self.filters["📻 Tog Radio"].setChecked(True)

        # Workspace – log viewer (HTML table format)
        self.workspace: QTextEdit = QTextEdit(self)
        self.workspace.setReadOnly(True)
        self.workspace.setFont(QFont("Courier New", 10))
        self.workspace.setStyleSheet(
            "background-color: #0F1B29; color: #FFD700; border: 1px solid #555;"
        )
        self.workspace.setFrameShape(QFrame.Shape.Box)
        self.workspace.setFrameShadow(QFrame.Shadow.Sunken)
        self.workspace.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        right_layout: QVBoxLayout = QVBoxLayout()
        right_layout.addLayout(order_layout)
        right_layout.addLayout(filter_panel)
        right_layout.addWidget(self.workspace)
        right_container: QWidget = QWidget()
        right_container.setLayout(right_layout)

        # ----- Main Layout -----
        main_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(right_container, 3)
        container: QWidget = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def set_order_asc(self) -> None:
        """Set log order to ascending (oldest first) and update workspace."""
        self.sort_order = "ASC"
        self.asc_button.setChecked(True)
        self.desc_button.setChecked(False)
        self.update_workspace()

    def set_order_desc(self) -> None:
        """Set log order to descending (newest first) and update workspace."""
        self.sort_order = "DESC"
        self.asc_button.setChecked(False)
        self.desc_button.setChecked(True)
        self.update_workspace()

    def load_logs(self) -> None:
        """Load a log file, enable toggles, populate name selections, and update workspace."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Text Files (*.txt)"
        )
        if file_path:
            logger.info(f"Loaded file: {file_path}")
            parser: LogParser = LogParser(file_path)
            self.raw_logs = parser.logs
            line_count: int = len(self.raw_logs)
            self.label.setText(
                f"Loaded: {os.path.basename(file_path)} ({line_count} lines)"
            )
            for btn in self.filters.values():
                btn.setEnabled(True)
            self.asc_button.setEnabled(True)
            self.desc_button.setEnabled(True)
            self.populate_name_selections()
            self.update_workspace()

    def populate_name_selections(self) -> None:
        """Populates the Interviewer and Interrogated groups based on log name frequencies."""
        # Clear previous selections.
        for layout in (self.interviewer_layout, self.interrogated_layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        self.interviewer_checkboxes = {}
        self.interrogated_checkboxes = {}

        # Count frequency of names using the same regex as in LogFormatter.
        freq: Dict[str, int] = {}
        for line in self.raw_logs:
            parsed = self.formatter.parse_line(line)
            if parsed and parsed.get("prefix"):
                name_match = self.formatter.NAME_PATTERN.match(parsed["prefix"])
                if name_match:
                    name = name_match.group("name")
                    freq[name] = freq.get(name, 0) + 1

        # Sort names by frequency descending.
        sorted_names = sorted(freq.items(), key=lambda x: -x[1])
        for name, count in sorted_names:
            text = f"{name} ({count})"
            cb_I = QCheckBox(text, self)
            cb_O = QCheckBox(text, self)
            # When zmieniamy jedną, wyłączamy drugą.
            cb_I.stateChanged.connect(
                lambda state, n=name: self.on_interviewer_changed(n, state)
            )
            cb_O.stateChanged.connect(
                lambda state, n=name: self.on_interrogated_changed(n, state)
            )
            self.interviewer_layout.addWidget(cb_I)
            self.interrogated_layout.addWidget(cb_O)
            self.interviewer_checkboxes[name] = cb_I
            self.interrogated_checkboxes[name] = cb_O

    def on_interviewer_changed(self, name: str, state: int) -> None:
        """Ensure a name selected as Interviewer is disabled in Interrogated group."""
        if state:  # Checked
            self.interrogated_checkboxes[name].setEnabled(False)
        else:
            self.interrogated_checkboxes[name].setEnabled(True)
        self.update_workspace()

    def on_interrogated_changed(self, name: str, state: int) -> None:
        """Ensure a name selected as Interrogated is disabled in Interviewer group."""
        if state:
            self.interviewer_checkboxes[name].setEnabled(False)
        else:
            self.interviewer_checkboxes[name].setEnabled(True)
        self.update_workspace()

    def get_selected_names(self) -> Tuple[List[str], List[str]]:
        """Return two lists: selected Interviewer names and selected Interrogated names."""
        selected_I = [
            name for name, cb in self.interviewer_checkboxes.items() if cb.isChecked()
        ]
        selected_O = [
            name for name, cb in self.interrogated_checkboxes.items() if cb.isChecked()
        ]
        return selected_I, selected_O

    def update_workspace(self) -> None:
        """
        Updates the workspace display according to toggle filters, log order, and
        (if checked) "Show only related" (filtering by selected Interviewer/Interrogated).

        The logs are displayed in an HTML table with two columns:
          - The first column shows the row index (display-only).
          - The second column shows the formatted log text. If "Show only related" is checked,
            only logs containing one of the selected names (in Interviewer or Interrogated) are shown,
            and a tag [I] or [O] (with numbering if more than one) is inserted after the action.
        """
        if not self.raw_logs:
            return

        # Pobierz stany przycisków filtrujących.
        show_date = self.filters["📅 Tog date"].isChecked()
        show_hour = self.filters["⏰ Tog hour"].isChecked()
        filter_me = self.filters["🙂 Tog /me"].isChecked()
        filter_do = self.filters["🔧 Tog /do"].isChecked()
        filter_OOC = self.filters["💬 Tog OOC"].isChecked()
        filter_PW = self.filters["✉️ Tog PW"].isChecked()
        filter_commands = self.filters["⌨️ Tog Commands"].isChecked()
        filter_unrecognized = self.filters["❓ Tog Unrecognized"].isChecked()
        filter_radio = self.filters["📻 Tog Radio"].isChecked()
        show_only_related = self.show_only_related_checkbox.isChecked()

        # Ustal kolejność logów.
        logs_to_iterate: List[str] = (
            self.raw_logs if self.sort_order == "ASC" else list(reversed(self.raw_logs))
        )
        table_rows: List[str] = []
        row_index: int = 1

        # Pobierz wybrane imiona.
        selected_I, selected_O = self.get_selected_names()

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

            # Filtracja radio: jeśli Tog Radio nie jest zaznaczony, wyklucz linie, które:
            # - są oznaczone jako radio (parsed["is_radio"] == True),
            # - zawierają '** [Kanał:' lub zaczynają się od "Audycja"
            if not filter_radio:
                if (
                    parsed.get("is_radio", False)
                    or "** [Kanał:" in line
                    or parsed["message"].lstrip().startswith("Audycja")
                ):
                    continue

            action: str = parsed["action"]
            # Filtracja dla poszczególnych akcji.
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

            # Jeśli "Show only related" jest zaznaczone i akcja nie należy do wyjątkowych,
            # to sprawdź, czy w logu występuje wybrane imię.
            def always_show(p: Dict[str, str]) -> bool:
                # Akcje "Komenda" oraz linie oznaczone jako radio zawsze wyświetlamy.
                return p["action"] == "Komenda" or p.get("is_radio", False)

            if show_only_related and not always_show(parsed):
                combined_text = (
                    parsed.get("prefix", "") + " " + parsed.get("message", "")
                ).lower()
                matching_I = [
                    name.lower() for name in selected_I if name.lower() in combined_text
                ]
                matching_O = [
                    name.lower() for name in selected_O if name.lower() in combined_text
                ]
                if not matching_I and not matching_O:
                    continue
                # Budujemy tag.
                tag = ""
                if matching_I:
                    if len(matching_I) == 1:
                        tag += "[I] "
                    else:
                        for i, n in enumerate(sorted(matching_I), start=1):
                            tag += f"[I{i}] "
                if matching_O:
                    if len(matching_O) == 1:
                        tag += "[O] "
                    else:
                        for i, n in enumerate(sorted(matching_O), start=1):
                            tag += f"[O{i}] "
                # Dołącz tag do wyniku – będzie wstawiony po akcji.
            else:
                tag = ""

            # Budujemy timestamp wg ustawień.
            date_part: str = parsed.get("date", "")
            time_part: str = parsed.get("time", "")
            new_timestamp: str = ""
            if show_date and date_part:
                new_timestamp += date_part
            if show_hour and time_part:
                new_timestamp += (" " if new_timestamp else "") + time_part
            new_timestamp = f"[{new_timestamp}]" if new_timestamp else ""

            timestamp_html = f'<span style="color: #00BFFF; font-weight: bold;">{new_timestamp}</span>'
            action_color = ACTION_COLOR_MAP.get(action, ACTION_COLOR_MAP["default"])
            action_html = f'<span style="color: {action_color}; font-weight: bold;">[{action}]</span>'
            prefix_html = ""
            if parsed.get("prefix", ""):
                prefix_html = f'<span style="color: #FFFFFF; font-weight: bold;">{parsed["prefix"]} </span>'
            message_html = f'<span style="color: #CCCCCC;">{parsed["message"]}</span>'
            # Jeśli mamy tag, wstaw go po akcji.
            if tag:
                tag_html = f'<span style="color: #FF69B4; font-weight: bold;">{tag}</span> '  # np. różowy
            else:
                tag_html = ""
            log_line_html = " ".join(
                [timestamp_html, action_html, tag_html, prefix_html, message_html]
            )
            row_html = (
                f"<td style='text-align: right; padding: 2px 5px; vertical-align: top;'>{row_index}</td>"
                f"<td style='padding: 2px 5px;'>{log_line_html}</td>"
            )
            table_rows.append(f"<tr>{row_html}</tr>")
            row_index += 1

        table_html = (
            "<table style='width: 100%; border-collapse: collapse;'>"
            + "".join(table_rows)
            + "</table>"
        )
        self.workspace.setHtml(table_html)

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
