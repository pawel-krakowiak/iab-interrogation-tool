"""
left_panel.py

Contains:
- Logo and 'Load Logs' button
- QGroupBox for Interviewer and Interrogated (wrapped in scroll areas, if desired)
- 'Show only related' checkbox
- Ordered selection logic for I/O
- Disables the same name in the other group upon selection
- Emits logsLoaded(List[str]) and namesUpdated(...) signals
"""

import os
import logging
from functools import partial
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QGroupBox, QCheckBox, QFileDialog, QScrollArea
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

from src.models.log_parser import LogParser
from src.models.log_formatter import LogFormatter

logger = logging.getLogger(__name__)


class LeftPanel(QWidget):
    """
    Left side panel with:
      - Logo
      - Load Logs button
      - Interviewer/Interrogated group boxes (optionally scrollable)
      - 'Show only related' checkbox
    Emits:
      - logsLoaded(List[str]): once logs are loaded from file
      - namesUpdated(List[str], List[str], bool): 
        * ordered list of interviewers, ordered list of interrogated, and show_only_related
    """

    logsLoaded = pyqtSignal(list)
    namesUpdated = pyqtSignal(list, list, bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("leftPanel")

        self.raw_logs: List[str] = []

        # Lists track the order in which interviewers/interrogated are selected
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
        Wrap group boxes in scroll areas if you'd like them to be scrollable.
        """
        # Logo
        logo_path = os.path.join(
            os.path.dirname(__file__), "../../resources/lssd_logo_bar.png"
        )
        pixmap = QPixmap(logo_path).scaled(300, 60, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create scroll areas for each group (optional, for large sets of names)
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Text Files (*.txt)"
        )
        if file_path:
            logger.info("Loaded file: %s", file_path)
            parser = LogParser(file_path)
            self.raw_logs = parser.logs
            self.logsLoaded.emit(self.raw_logs)
            self._populate_name_selections()

    def _populate_name_selections(self) -> None:
        """
        Create checkboxes for each discovered name in logs, sorted by descending frequency.
        Use the raw name for logic keys, and a display string for user text.
        """
        # Clear old checkboxes
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

        freq = {}
        formatter = LogFormatter()
        for line in self.raw_logs:
            parsed = formatter.parse_line(line)
            if parsed and parsed.get("prefix"):
                match = formatter.NAME_PATTERN.match(parsed["prefix"])
                if match:
                    raw_name = match.group("name")
                    freq[raw_name] = freq.get(raw_name, 0) + 1

        # Sort by descending frequency
        sorted_names = sorted(freq.items(), key=lambda x: -x[1])
        for (raw_name, count) in sorted_names:
            display_text = f"{raw_name} ({count})"
            cb_i = QCheckBox(display_text, self)
            cb_o = QCheckBox(display_text, self)

            # Connect partial with the raw_name for consistent lookups
            cb_i.stateChanged.connect(partial(self._on_interviewer_changed, raw_name))
            cb_o.stateChanged.connect(partial(self._on_interrogated_changed, raw_name))

            # Add to group layouts
            self.interviewer_layout.addWidget(cb_i)
            self.interrogated_layout.addWidget(cb_o)

            # Store references in dictionaries
            self.interviewer_checkboxes[raw_name] = cb_i
            self.interrogated_checkboxes[raw_name] = cb_o

        # Emit to update the rest of the UI
        self._emit_names_updated()

    def _on_interviewer_changed(self, raw_name: str, state: int) -> None:
        is_checked = (state == Qt.CheckState.Checked)

        if is_checked:
            if raw_name not in self._interviewer_order:
                self._interviewer_order.append(raw_name)

            if raw_name in self.interrogated_checkboxes:
                other = self.interrogated_checkboxes[raw_name]
                other.setChecked(False)
                other.setCheckable(False)
                other.setEnabled(False)
                if raw_name in self._interrogated_order:
                    self._interrogated_order.remove(raw_name)
        else:
            if raw_name in self._interviewer_order:
                self._interviewer_order.remove(raw_name)

            if raw_name in self.interrogated_checkboxes:
                other = self.interrogated_checkboxes[raw_name]
                other.setCheckable(True)
                other.setEnabled(True)

        self._emit_names_updated()


    def _on_interrogated_changed(self, raw_name: str, state: int) -> None:
        is_checked = (state == Qt.CheckState.Checked)

        if is_checked:
            if raw_name not in self._interrogated_order:
                self._interrogated_order.append(raw_name)

            if raw_name in self.interviewer_checkboxes:
                other = self.interviewer_checkboxes[raw_name]
                other.setChecked(False)
                other.setCheckable(False)
                other.setEnabled(False)
                if raw_name in self._interviewer_order:
                    self._interviewer_order.remove(raw_name)
        else:
            if raw_name in self._interrogated_order:
                self._interrogated_order.remove(raw_name)

            if raw_name in self.interviewer_checkboxes:
                other = self.interviewer_checkboxes[raw_name]
                other.setCheckable(True)
                other.setEnabled(True)

        self._emit_names_updated()


    def _emit_names_updated(self) -> None:
        """
        Emits the ordered Interviewers, ordered Interrogated, and
        whether 'Show only related' is checked.
        """
        show_related = self.show_only_related_checkbox.isChecked()
        self.namesUpdated.emit(self._interviewer_order, self._interrogated_order, show_related)
