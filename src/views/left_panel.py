"""
left_panel.py

Handles:
- Logo and 'Load Logs' button
- QGroupBox for Interviewer and Interrogated (with scroll areas)
- 'Show only related' checkbox
- Disables selection of the same person in both groups
- Emits logsLoaded(List[str]) and namesUpdated(...) signals
"""

import os
import logging
from functools import partial
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QFileDialog,
    QScrollArea,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

from src.models.log_parser import LogParser
from src.models.log_formatter import LogFormatter

logger = logging.getLogger(__name__)


class LeftPanel(QWidget):
    """
    Left-side panel with:
      - Logo
      - Load Logs button
      - Interviewer/Interrogated selection (with mutual exclusion)
      - 'Show only related' checkbox
    Emits:
      - logsLoaded(List[str]): once logs are loaded
      - namesUpdated(List[str], List[str], bool):
        * ordered list of interviewers, ordered list of interrogated, and show_only_related flag
    """

    logsLoaded = pyqtSignal(list)  # Emits raw log list
    namesUpdated = pyqtSignal(
        list, list, bool
    )  # Emits updated interviewers/interrogated lists

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("leftPanel")

        self.raw_logs: List[str] = []

        # Track selected interviewers/interrogated
        self._interviewer_order: List[str] = []
        self._interrogated_order: List[str] = []

        # Dicts from raw_name -> QCheckBox
        self.interviewer_checkboxes: Dict[str, QCheckBox] = {}
        self.interrogated_checkboxes: Dict[str, QCheckBox] = {}

        # UI elements
        self.logo_label = QLabel(self)
        self.load_button = QPushButton("📂 Load Logs", self)

        self.interviewer_group = QGroupBox("Interviewer [I]", self)
        self.interviewer_layout = QVBoxLayout()
        self.interviewer_group.setLayout(self.interviewer_layout)

        self.interrogated_group = QGroupBox("Interrogated/POI [O]", self)
        self.interrogated_layout = QVBoxLayout()
        self.interrogated_group.setLayout(self.interrogated_layout)

        self.show_only_related_checkbox = QCheckBox("Show only related", self)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """
        Sets up layout: logo, load button, group boxes, 'Show only related'.
        Wraps group boxes in scroll areas.
        """
        # Logo
        logo_path = os.path.join(
            os.path.dirname(__file__), "../../resources/lssd_logo_bar.png"
        )
        pixmap = QPixmap(logo_path).scaled(300, 60, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create scroll areas for each group
        interviewer_scroll = QScrollArea(self)
        interviewer_scroll.setWidget(self.interviewer_group)
        interviewer_scroll.setWidgetResizable(True)

        interrogated_scroll = QScrollArea(self)
        interrogated_scroll.setWidget(self.interrogated_group)
        interrogated_scroll.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.logo_label)
        layout.addWidget(self.load_button)
        layout.addWidget(interviewer_scroll)
        layout.addWidget(interrogated_scroll)
        layout.addWidget(self.show_only_related_checkbox)
        layout.addStretch()
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        """
        Connect button clicks and checkbox signals to internal slots.
        """
        self.load_button.clicked.connect(self._on_load_clicked)
        self.show_only_related_checkbox.stateChanged.connect(self._emit_names_updated)

    def _on_load_clicked(self) -> None:
        """
        Opens a file dialog to load logs. Emits logsLoaded, then populates name selections.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Log File", "", "Text Files (*.txt)")
        if not file_path:
            logger.info("No file selected.")
            return

        if file_path:
            logger.info("📂 Loaded file: %s", file_path)
            parser = LogParser(file_path)
            self.raw_logs = parser.logs
            self.logsLoaded.emit(self.raw_logs)
            self._populate_name_selections()

    def _populate_name_selections(self) -> None:
        """
        Tworzy checkboxy dla każdej wykrytej osoby w logach, sortując je według liczby wystąpień.
        """
        # Czyszczenie starej listy
        for layout in (self.interviewer_layout, self.interrogated_layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        self.interviewer_checkboxes.clear()
        self.interrogated_checkboxes.clear()
        self._interviewer_order.clear()
        self._interrogated_order.clear()

        # Analiza logów i zliczanie osób
        freq = {}
        formatter = LogFormatter()
        for line in self.raw_logs:
            parsed = formatter.parse_line(line)
            if parsed and parsed.get("prefix"):
                match = formatter.NAME_PATTERN.match(parsed["prefix"])
                if match:
                    raw_name = match.group("name")
                    freq[raw_name] = freq.get(raw_name, 0) + 1

        # Sortowanie według liczby wystąpień
        sorted_names = sorted(freq.items(), key=lambda x: -x[1])

        for raw_name, count in sorted_names:
            display_text = f"{raw_name} ({count})"
            cb_i = QCheckBox(display_text, self)
            cb_o = QCheckBox(display_text, self)

            # Obsługa wzajemnego wykluczania wyboru
            cb_i.stateChanged.connect(partial(self._on_interviewer_changed, raw_name))
            cb_o.stateChanged.connect(partial(self._on_interrogated_changed, raw_name))

            # Dodanie do układu
            self.interviewer_layout.addWidget(cb_i)
            self.interrogated_layout.addWidget(cb_o)

            # Przechowywanie referencji do checkboxów
            self.interviewer_checkboxes[raw_name] = cb_i
            self.interrogated_checkboxes[raw_name] = cb_o

        # Emitowanie zaktualizowanej listy
        self._emit_names_updated()


    def _on_interviewer_changed(self, raw_name: str, state: int) -> None:
        """
        Obsługuje zaznaczenie osoby jako Interviewer i dezaktywuje ją w Interrogated.
        """
        is_checked = state == Qt.CheckState.Checked
    
        if is_checked:
            if raw_name not in self._interviewer_order:
                self._interviewer_order.append(raw_name)
    
            # Wyłącz checkbox w Interrogated
            if raw_name in self.interrogated_checkboxes:
                self.interrogated_checkboxes[raw_name].setChecked(False)
                self.interrogated_checkboxes[raw_name].setEnabled(False)
        else:
            if raw_name in self._interviewer_order:
                self._interviewer_order.remove(raw_name)
    
            # Włącz checkbox w Interrogated
            if raw_name in self.interrogated_checkboxes:
                self.interrogated_checkboxes[raw_name].setEnabled(True)
    
        self._emit_names_updated()
    
    
    def _on_interrogated_changed(self, raw_name: str, state: int) -> None:
        """
        Obsługuje zaznaczenie osoby jako Interrogated i dezaktywuje ją w Interviewer.
        """
        is_checked = state == Qt.CheckState.Checked
    
        if is_checked:
            if raw_name not in self._interrogated_order:
                self._interrogated_order.append(raw_name)
    
            # Wyłącz checkbox w Interviewer
            if raw_name in self.interviewer_checkboxes:
                self.interviewer_checkboxes[raw_name].setChecked(False)
                self.interviewer_checkboxes[raw_name].setEnabled(False)
        else:
            if raw_name in self._interrogated_order:
                self._interrogated_order.remove(raw_name)
    
            # Włącz checkbox w Interviewer
            if raw_name in self.interviewer_checkboxes:
                self.interviewer_checkboxes[raw_name].setEnabled(True)
    
        self._emit_names_updated()


    def _emit_names_updated(self) -> None:
        """
        Emits the ordered Interviewers, ordered Interrogated, and
        whether 'Show only related' is checked.
        """
        show_related = self.show_only_related_checkbox.isChecked()
        logger.debug(
            f"🔹 Emitting Names -> Interviewers: {self._interviewer_order}, Interrogated: {self._interrogated_order}, ShowOnlyRelated: {show_related}"
        )
        self.namesUpdated.emit(
            self._interviewer_order, self._interrogated_order, show_related
        )
