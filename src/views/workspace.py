"""
src/views/workspace.py

Displays logs in an HTML table with advanced filtering logic:
- Toggles for date/hour, /me, /do, OOC, PW, radio, etc.
- ASC/DESC order
- Always label lines containing selected interviewers or interrogated with [I], [I1], etc. or [O], [O1], ...
- Only hide lines that don't involve them if show_only_related is True.
"""

import logging
from typing import List, Dict, Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from src.models.log_formatter import LogFormatter, ACTION_COLOR_MAP

logger = logging.getLogger(__name__)


class Workspace(QWidget):
    """
    A text-based workspace that shows logs in HTML form, respecting toggles, order,
    and interviewers/interrogated selection + show-only-related logic.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._raw_logs: List[str] = []
        self._formatter = LogFormatter()

        # Toggles from RightPanel: "Tog date", "Tog hour", etc.
        self._toggles: Dict[str, bool] = {}
        self._order: str = "ASC"

        # For labeling: interviewer_order, interrogated_order
        self._interviewer_order: List[str] = []
        self._interrogated_order: List[str] = []
        self._show_only_related: bool = False

        # UI
        layout = QVBoxLayout(self)
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont("Courier New", 10))
        self._text_edit.setLineWrapMode(
            QTextEdit.LineWrapMode.NoWrap
        )  # horizontal scroll
        self._text_edit.setStyleSheet(
            "background-color: #0F1B29; color: #FFD700; border: 1px solid #555;"
        )

        layout.addWidget(self._text_edit)
        self.setLayout(layout)

    # ----- Called by RightPanel -----

    def set_raw_logs(self, logs: List[str]) -> None:
        """Store the raw logs for display."""
        self._raw_logs = logs
        self.update_view()

    def on_filter_toggles_updated(self, toggles: Dict[str, bool]) -> None:
        """Updates filter toggles and refreshes the log view."""
        self._toggles = toggles
        self.update_view()

    def on_order_changed(self, order: str) -> None:
        """ASC or DESC from the right panel."""
        self._order = order
        self.update_view()

    # ----- Called by LeftPanel -> RightPanel -> This Workspace -----

    def set_selected_names(
        self,
        interviewer_order: List[str],
        interrogated_order: List[str],
        show_related: bool,
    ) -> None:
        """
        Receives the (ordered) interviewers, (ordered) interrogated,
        and whether to show only lines that contain them (if not Komenda or radio).
        """
        self._interviewer_order = interviewer_order[:]
        self._interrogated_order = interrogated_order[:]
        self._show_only_related = show_related
        logger.debug(
            f"📌 Workspace Received -> Interviewers: {self._interviewer_order}, Interrogated: {self._interrogated_order}"
        )
        self.update_view()

    # ----- Render -----

    def update_view(self) -> None:
        """
        Rebuilds the workspace display based on toggles, ordering, and selected names.
        - Toggles for date/hour, /me, /do, OOC, PW, commands, unrecognized, radio
        - ASC/DESC sorting
        - '[I]' (green) prefix for interviewers
        - '[O]' (red) prefix for interrogated persons
        - Filters out unrelated messages if 'Show only related' is enabled (to be implemented)
        """
        if not self._raw_logs:
            self._text_edit.setHtml("<p>No logs loaded</p>")
            return

        # Retrieve current toggle states (default to True)
        show_date = self._toggles.get("📅 Tog date", True)
        show_hour = self._toggles.get("⏰ Tog hour", True)
        filter_me = self._toggles.get("🙂 Tog /me", True)
        filter_do = self._toggles.get("🖼️ Tog /do", True)
        filter_ooc = self._toggles.get("💬 Tog OOC", True)
        filter_pw = self._toggles.get("📩 Tog PW", True)
        filter_commands = self._toggles.get("🔧 Tog Commands", True)
        filter_unrecognized = self._toggles.get("🕵️ Tog Unrecognized", True)
        filter_radio = self._toggles.get("🚔 Tog Radio", True)
        show_only_related = self._show_only_related

        # Sort logs
        logs_to_iterate = self._raw_logs[:]
        if self._order == "DESC":
            logs_to_iterate.reverse()

        table_rows = []
        row_index = 1

        # Selected persons
        selected_I = self._interviewer_order
        selected_O = self._interrogated_order

        for line in logs_to_iterate:
            parsed = self._formatter.parse_line(line)

            # If the line does not match the expected pattern, treat as unrecognized
            if not parsed:
                if filter_unrecognized:
                    row_html = f"<td>{row_index}</td><td><pre>{line}</pre></td>"
                    table_rows.append(f"<tr>{row_html}</tr>")
                    row_index += 1
                continue

            action = parsed["action"]
            prefix = parsed.get("prefix", "").strip()
            message = parsed["message"]

            # Apply action-based filters
            if action == "Akcja /me" and not filter_me:
                continue
            if action == "Akcja /do" and not filter_do:
                continue
            if action == "Czat OOC" and not filter_ooc:
                continue
            if action == "PW" and not filter_pw:
                continue
            if action == "Komenda" and not filter_commands:
                continue

            # If the message is a radio transmission (e.g., ** [Channel: XYZ])
            if not filter_radio and ("Kanał:" in message):
                continue

            # ---------- ADDING PREFIXES [I] AND [O] ----------
            tag = ""
            if prefix in selected_I:
                tag = '<span style="color: #00FF00; font-weight: bold;">[I]</span> '
            elif prefix in selected_O:
                tag = '<span style="color: #FF0000; font-weight: bold;">[O]</span> '

            # Construct timestamp based on toggles
            timestamp_parts = []
            if show_date and parsed.get("date"):
                timestamp_parts.append(parsed["date"])
            if show_hour and parsed.get("time"):
                timestamp_parts.append(parsed["time"])
            new_timestamp = f"[{' '.join(timestamp_parts)}]" if timestamp_parts else ""

            # Formatting HTML
            timestamp_html = f'<span style="color: #00BFFF; font-weight: bold;">{new_timestamp}</span>'
            action_color = ACTION_COLOR_MAP.get(action, ACTION_COLOR_MAP["default"])
            action_html = f'<span style="color: {action_color}; font-weight: bold;">[{action}]</span>'
            prefix_html = (
                f'{tag}<span style="color: #FFFFFF; font-weight: bold;">{prefix} </span>'
                if prefix
                else ""
            )
            message_html = f'<span style="color: #CCCCCC;">{message}</span>'

            row_html = f"<td>{row_index}</td><td>{timestamp_html} {action_html} {prefix_html} {message_html}</td>"
            table_rows.append(f"<tr>{row_html}</tr>")
            row_index += 1

        # Render the table
        table_html = "<table>" + "".join(table_rows) + "</table>"
        self._text_edit.setHtml(table_html)
