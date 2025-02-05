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
        self.update_view()

    # ----- Render -----

    def update_view(self) -> None:
        """
        Rebuilds the workspace display based on toggles, ordering, and selected names.
        Matches the old main_window.py logic:
          - Toggles for date/hour, /me, /do, OOC, PW, commands, unrecognized, radio
          - ASC/DESC sort
          - 'Show only related' filters
          - [I]/[O] tagging if multiple interviewers/interrogated
        """
        if not self._raw_logs:
            self._text_edit.setHtml("<p>No logs loaded</p>")
            return

        # Retrieve toggles (default to True, matching old code)
        show_date = self._toggles.get("📅 Tog date", True)
        show_hour = self._toggles.get("⏰ Tog hour", True)
        filter_me = self._toggles.get("🙂 Tog /me", True)
        filter_do = self._toggles.get("🖼️ Tog /do", True)
        filter_ooc = self._toggles.get("💬 Tog OOC", True)
        filter_pw = self._toggles.get("📩 Tog PW", True)
        filter_commands = self._toggles.get("🔧 Tog Commands", True)
        filter_unrecognized = self._toggles.get("🕵️ Tog Unrecognized", True)
        filter_radio = self._toggles.get("🚔 Tog Radio", True)

        # "Show only related" is stored separately
        show_only_related = self._show_only_related

        # Sort logs
        logs_to_iterate = self._raw_logs[:]
        if self._order == "DESC":
            logs_to_iterate.reverse()

        table_rows = []
        row_index = 1

        # Gather selected names
        selected_I = self._interviewer_order
        selected_O = self._interrogated_order

        for line in logs_to_iterate:
            parsed = self._formatter.parse_line(line)

            # If unrecognized
            if not parsed:
                if filter_unrecognized:
                    row_html = f"<td>{row_index}</td><td><pre>{line}</pre></td>"
                    table_rows.append(f"<tr>{row_html}</tr>")
                    row_index += 1
                continue

            # Radio filter
            if not filter_radio and parsed.get("is_radio", False):
                continue

            action = parsed["action"]

            # Action-based filters
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

            # 'Show only related' logic:
            # Lines with "Komenda" or is_radio are always shown
            always_show = parsed["action"] == "Komenda" or parsed.get("is_radio", False)
            combined_text = (
                f"{parsed.get('prefix', '')} {parsed.get('message', '')}".lower()
            )
            matching_I = [
                nm.lower() for nm in selected_I if nm.lower() in combined_text
            ]
            matching_O = [
                nm.lower() for nm in selected_O if nm.lower() in combined_text
            ]

            # Build the [I]/[O] tags
            tag = ""
            if matching_I:
                tag += (
                    "[I] "
                    if len(matching_I) == 1
                    else "".join(
                        f"[I{i}] " for i, _ in enumerate(sorted(matching_I), start=1)
                    )
                )
            if matching_O:
                tag += (
                    "[O] "
                    if len(matching_O) == 1
                    else "".join(
                        f"[O{i}] " for i, _ in enumerate(sorted(matching_O), start=1)
                    )
                )

            # If 'Show Only Related' is enabled, filter out unrelated logs
            if show_only_related and not always_show and not (matching_I or matching_O):
                continue

            # Build timestamp
            date_part = parsed.get("date", "")
            time_part = parsed.get("time", "")
            new_timestamp = (
                f"[{date_part} {time_part}]"
                if (show_date and date_part) or (show_hour and time_part)
                else ""
            )

            # Format log line
            timestamp_html = f'<span style="color: #00BFFF; font-weight: bold;">{new_timestamp}</span>'
            action_color = ACTION_COLOR_MAP.get(action, ACTION_COLOR_MAP["default"])
            action_html = f'<span style="color: {action_color}; font-weight: bold;">[{action}]</span>'
            prefix_html = (
                f'<span style="color: #FFFFFF; font-weight: bold;">{parsed["prefix"]} </span>'
                if parsed.get("prefix")
                else ""
            )
            message_html = f'<span style="color: #CCCCCC;">{parsed["message"]}</span>'
            tag_html = (
                f'<span style="color: #FF69B4; font-weight: bold;">{tag}</span> '
                if tag
                else ""
            )

            row_html = f"<td>{row_index}</td><td>{timestamp_html} {action_html} {tag_html} {prefix_html} {message_html}</td>"
            table_rows.append(f"<tr>{row_html}</tr>")
            row_index += 1

        table_html = "<table>" + "".join(table_rows) + "</table>"
        self._text_edit.setHtml(table_html)
