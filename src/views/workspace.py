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
        - '[I]' (green) prefix for interviewers
        - '[O]' (red) prefix for interrogated persons
        - Matches names only when they are the speaker (not just mentioned)
        - Does NOT apply tags to 'Komenda' (starts with '/' or '.') or 'PW' (starts with '[')
        - Applies all filtering toggles correctly
        - Fixes 'Show Only Related' to filter out unrelated radio messages
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
        filter_action_tags = self._toggles.get("🔖 Tog Action Tags", True)
        show_only_related = self._show_only_related

        # Sort logs
        logs_to_iterate = self._raw_logs[:]
        if self._order == "DESC":
            logs_to_iterate.reverse()

        table_rows = []
        row_index = 1

        # Selected persons
        selected_I = set(self._interviewer_order)
        selected_O = set(self._interrogated_order)

        for line in logs_to_iterate:
            parsed = self._formatter.parse_line(line)
            if not parsed:
                if filter_unrecognized:
                    continue  # Now actually hides unrecognized logs!
                row_html = f"<td>{row_index}</td><td><pre>{line}</pre></td>"
                table_rows.append(f"<tr>{row_html}</tr>")
                row_index += 1
                continue

            action = parsed["action"]
            prefix = parsed.get("prefix", "").strip()
            message = parsed["message"].strip()
            is_radio_message = parsed.get("is_radio", False)

            # 🔹 FILTERS BASED ON TOGGLES
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

            # 🔹 FILTER RADIO
            if not filter_radio and is_radio_message:
                continue

            # 🔹 FILTER 'SHOW ONLY RELATED'
            always_show = action == "Komenda"
            combined_text = f"{prefix} {message}".strip().lower()
            matching_I = [
                nm.lower() for nm in selected_I if nm.lower() in combined_text
            ]
            matching_O = [
                nm.lower() for nm in selected_O if nm.lower() in combined_text
            ]

            if show_only_related and not always_show and not (matching_I or matching_O):
                if (
                    is_radio_message
                    and prefix.lower() not in selected_I
                    and prefix.lower() not in selected_O
                ):
                    continue  # Hides radio messages if the speaker is not in the selected list
                if not is_radio_message:
                    continue  # Hides non-radio messages if they are unrelated

            # 🔹 IGNORE [I] and [O] FOR COMMANDS AND PW
            is_command_or_pw = (
                message.startswith("/")
                or message.startswith(".")
                or message.startswith("[")
            )

            # 🔹 ADDING PREFIXES [I] AND [O] – only if the person WROTE the message
            tag = ""
            if not is_command_or_pw:
                full_text = f"{prefix} {message}".strip()
                if any(name.lower() in full_text.lower() for name in selected_I):
                    tag = '<span style="color: #00FF00; font-weight: bold;">[I]</span> '
                elif any(name.lower() in full_text.lower() for name in selected_O):
                    tag = '<span style="color: #FF0000; font-weight: bold;">[O]</span> '

            # 🔹 REMOVE ACTION TAGS IF TOG ACTION TAGS IS OFF
            if not filter_action_tags:
                action_html = ""
            else:
                action_color = ACTION_COLOR_MAP.get(action, ACTION_COLOR_MAP["default"])
                action_html = f'<span style="color: {action_color}; font-weight: bold;">[{action}]</span>'

            # 🔹 CONSTRUCT TIMESTAMP
            timestamp_parts = []
            if show_date and parsed.get("date"):
                timestamp_parts.append(parsed["date"])
            if show_hour and parsed.get("time"):
                timestamp_parts.append(parsed["time"])
            new_timestamp = f"[{' '.join(timestamp_parts)}]" if timestamp_parts else ""

            # 🔹 FORMAT HTML
            timestamp_html = f'<span style="color: #00BFFF; font-weight: bold;">{new_timestamp}</span>'
            prefix_html = (
                f'<span style="color: #FFFFFF; font-weight: bold;">{prefix} </span>'
                if prefix
                else ""
            )
            message_html = f'<span style="color: #CCCCCC;">{message}</span>'

            # 🔹 BUILD TABLE ROW
            row_html = f"<td>{row_index}</td><td>{timestamp_html} {tag}{action_html} {prefix_html} {message_html}</td>"
            table_rows.append(f"<tr>{row_html}</tr>")
            row_index += 1

        # 🔹 RENDER TABLE
        table_html = "<table>" + "".join(table_rows) + "</table>"
        self._text_edit.setHtml(table_html)
