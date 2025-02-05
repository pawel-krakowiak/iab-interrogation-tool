"""
src/views/right_panel.py

Contains:
- Order controls (ASC/DESC)
- Filter toggles
- Workspace for advanced log display
- Receives name selection updates (with show_related) from LeftPanel
"""

import logging
from functools import partial
from typing import List, Dict
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

from src.views.workspace import Workspace

logger = logging.getLogger(__name__)


class RightPanel(QWidget):
    """
    Right side panel with:
      - Asc/Desc buttons
      - Filter toggles
      - Workspace for displaying logs

    Signals:
      - filterTogglesUpdated(dict[str, bool]): toggles changed
      - orderChanged(str): 'ASC' or 'DESC'
    """

    filterTogglesUpdated = pyqtSignal(dict)  # Example: {"📅 Tog date": True, ...}
    orderChanged = pyqtSignal(str)  # Example: "ASC" or "DESC"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._raw_logs: List[str] = []
        self._sort_order: str = "ASC"

        self._toggle_names: List[str] = [
            "📅 Tog date",
            "⏰ Tog hour",
            "🙂 Tog /me",
            "🖼️ Tog /do",
            "💬 Tog OOC",
            "📩 Tog PW",
            "🔧 Tog Commands",
            "🕵️ Tog Unrecognized",
            "🚔 Tog Radio",
        ]
        self._toggles: Dict[str, QPushButton] = {}

        self._order_label = QLabel("Logs order", self)
        self._asc_button = QPushButton("ASC ⬆")
        self._desc_button = QPushButton("DESC ⬇")

        self.workspace = Workspace()

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """
        Creates layout with order controls, toggles, and workspace.
        """
        self._order_label.setFont(QFont("Arial", 12))
        self._order_label.setStyleSheet("color: #FFD700;")

        self._asc_button.setCheckable(True)
        self._desc_button.setCheckable(True)
        self._asc_button.setChecked(True)  # Default is ASC order

        order_layout = QHBoxLayout()
        order_layout.addWidget(self._order_label)
        order_layout.addWidget(self._asc_button)
        order_layout.addWidget(self._desc_button)
        order_layout.addStretch()

        filter_layout = QHBoxLayout()
        for name in self._toggle_names:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setEnabled(False)  # Will be enabled once logs are loaded
            filter_layout.addWidget(btn)
            self._toggles[name] = btn
        filter_layout.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(order_layout)
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.workspace)
        self.setLayout(main_layout)

    def _connect_signals(self) -> None:
        """
        Connect toggles and order buttons to internal slots.
        """
        self._asc_button.clicked.connect(self._on_asc_clicked)
        self._desc_button.clicked.connect(self._on_desc_clicked)

        # Connect each toggle button with its handler
        for name, btn in self._toggles.items():
            btn.toggled.connect(partial(self._on_toggle_changed, name))

    # -------------------- ORDER --------------------

    def _on_asc_clicked(self) -> None:
        """Set order to ASC and emit signal."""
        if self._sort_order != "ASC":
            self._sort_order = "ASC"
            self._asc_button.setChecked(True)
            self._desc_button.setChecked(False)
            self.orderChanged.emit("ASC")
            self.workspace.on_order_changed("ASC")

    def _on_desc_clicked(self) -> None:
        """Set order to DESC and emit signal."""
        if self._sort_order != "DESC":
            self._sort_order = "DESC"
            self._asc_button.setChecked(False)
            self._desc_button.setChecked(True)
            self.orderChanged.emit("DESC")
            self.workspace.on_order_changed("DESC")

    # -------------------- TOGGLES --------------------

    def _on_toggle_changed(self, toggle_name: str, checked: bool) -> None:
        """
        Emit current states of all toggles whenever any single toggle changes.
        """
        states = {name: btn.isChecked() for name, btn in self._toggles.items()}
        logger.debug(f"🔄 Toggle Updated -> {toggle_name}: {checked}")
        self.filterTogglesUpdated.emit(states)
        self.workspace.on_filter_toggles_updated(states)

    # -------------------- EXTERNAL INTERFACE --------------------

    def on_logs_loaded(self, logs: List[str]) -> None:
        """
        Called by MainWindow/LeftPanel when logs are loaded.
        Enables toggles, sets logs in the workspace, triggers an update.
        """
        logger.debug(f"📂 Logs Loaded -> {len(logs)} entries")
        self._raw_logs = logs
        for btn in self._toggles.values():
            if not btn.isEnabled():
                btn.setEnabled(True)

        # By default, set all toggles to True (matching old behavior)
        for name in self._toggle_names:
            self._toggles[name].setChecked(True)

        # Let the workspace know about the logs
        self.workspace.set_raw_logs(logs)
        self.workspace.update_view()

    def on_names_updated(
        self, interviewers: List[str], interrogated: List[str], show_related: bool
    ) -> None:
        """
        Called when LeftPanel emits 'namesUpdated' with the ordered interviewers,
        ordered interrogated, and show_only_related flag.
        We pass these to the Workspace, then update_view.
        """
        logger.debug(
            f"📝 Names Updated -> Interviewers: {interviewers}, Interrogated: {interrogated}, ShowOnlyRelated: {show_related}"
        )
        self.workspace.set_selected_names(interviewers, interrogated, show_related)
        self.workspace.update_view()

    @property
    def sort_order(self) -> str:
        """
        Returns the current sort order, e.g. 'ASC' or 'DESC'.
        """
        return self._sort_order
