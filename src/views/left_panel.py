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

        self.interviewer_group = QGroupBox("Interviewer/LEA [I]", self)
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Text Files (*.txt)"
        )
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
        Creates checkboxes for each discovered name in logs, sorted by frequency.
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

        # Sort names by frequency
        sorted_names = sorted(freq.items(), key=lambda x: -x[1])
        for raw_name, count in sorted_names:
            display_text = f"{raw_name} ({count})"
            cb_i = QCheckBox(display_text, self)
            cb_o = QCheckBox(display_text, self)

            # Connect with the raw_name
            cb_i.stateChanged.connect(
                partial(self._on_interviewer_changed, display_text)
            )
            cb_o.stateChanged.connect(
                partial(self._on_interrogated_changed, display_text)
            )

            # Add to group layouts
            self.interviewer_layout.addWidget(cb_i)
            self.interrogated_layout.addWidget(cb_o)

            # Store references
            self.interviewer_checkboxes[raw_name] = cb_i
            self.interrogated_checkboxes[raw_name] = cb_o

        # Emit updated names
        self._emit_names_updated()

    def _on_interviewer_changed(self, raw_display_text: str, state: int) -> None:
        """
        Handles checking/unchecking of Interviewer checkboxes.
        Ensures the same name is disabled in Interrogated.
        """
        raw_name = raw_display_text.split(" (")[0]  # Remove frequency count

        # Ensure correct checkbox state
        is_checked = state == Qt.CheckState.Checked.value
        logger.debug(
            f"🟢 Interviewer Checkbox Clicked -> {raw_name}, State: {state}, is_checked: {is_checked}"
        )

        if is_checked:
            if raw_name not in self._interviewer_order:
                self._interviewer_order.append(raw_name)
                logger.debug(f"✅ Added to Interviewers: {raw_name}")

            # Disable in Interrogated
            if raw_name in self.interrogated_checkboxes:
                self.interrogated_checkboxes[raw_name].setChecked(False)
                self.interrogated_checkboxes[raw_name].setEnabled(False)
                logger.debug(f"🚫 Disabled '{raw_name}' in Interrogated")
        else:
            if raw_name in self._interviewer_order:
                self._interviewer_order.remove(raw_name)
                logger.debug(f"❌ Removed from Interviewers: {raw_name}")

            # Re-enable in Interrogated (only if it wasn't manually disabled)
            if raw_name in self.interrogated_checkboxes:
                self.interrogated_checkboxes[raw_name].setEnabled(True)
                logger.debug(f"🔓 Re-enabled '{raw_name}' in Interrogated")

        self._emit_names_updated()

    def _on_interrogated_changed(self, raw_display_text: str, state: int) -> None:
        """
        Handles checking/unchecking of Interrogated checkboxes.
        Ensures the same name is disabled in Interviewer.
        """
        raw_name = raw_display_text.split(" (")[0]  # Remove frequency count

        # Ensure correct checkbox state
        is_checked = state == Qt.CheckState.Checked.value
        logger.debug(
            f"🔴 Interrogated Checkbox Clicked -> {raw_name}, State: {state}, is_checked: {is_checked}"
        )

        if is_checked:
            if raw_name not in self._interrogated_order:
                self._interrogated_order.append(raw_name)
                logger.debug(f"✅ Added to Interrogated: {raw_name}")

            # Disable in Interviewer
            if raw_name in self.interviewer_checkboxes:
                self.interviewer_checkboxes[raw_name].setChecked(False)
                self.interviewer_checkboxes[raw_name].setEnabled(False)
                logger.debug(f"🚫 Disabled '{raw_name}' in Interviewer")
        else:
            if raw_name in self._interrogated_order:
                self._interrogated_order.remove(raw_name)
                logger.debug(f"❌ Removed from Interrogated: {raw_name}")

            # Re-enable in Interviewer (only if it wasn't manually disabled)
            if raw_name in self.interviewer_checkboxes:
                self.interviewer_checkboxes[raw_name].setEnabled(True)
                logger.debug(f"🔓 Re-enabled '{raw_name}' in Interviewer")

        self._emit_names_updated()

    def _emit_names_updated(self) -> None:
        """
        Emits the ordered Interviewers, ordered Interrogated, and
        whether 'Show only related' is checked.
        """
        show_related = self.show_only_related_checkbox.isChecked()

        # Log debugging information
        logger.debug(
            f"🔹 Emitting Names -> Interviewers: {self._interviewer_order}, Interrogated: {self._interrogated_order}, ShowOnlyRelated: {show_related}"
        )

        # Emit signal with updated values
        self.namesUpdated.emit(
            list(self._interviewer_order), list(self._interrogated_order), show_related
        )
