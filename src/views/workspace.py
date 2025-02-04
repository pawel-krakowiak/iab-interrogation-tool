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
        self._text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # horizontal scroll
        self._text_edit.setStyleSheet(
            "background-color: #0F1B29; color: #FFD700; border: 1px solid #555;"
        )

        layout.addWidget(self._text_edit)
        self.setLayout(layout)

    # ----- Called by RightPanel -----

    def set_raw_logs(self, logs: List[str]) -> None:
        """Store the raw logs for display."""
        self._raw_logs = logs


    def on_filter_toggles_updated(self, toggles: Dict[str, bool]) -> None:
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
        show_related: bool
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
                    # Show as <pre>
                    row_html = (
                        f"<td style='text-align: right; padding: 2px 5px;'>{row_index}</td>"
                        f"<td><pre style='margin: 0;'>{line}</pre></td>"
                    )
                    table_rows.append(f"<tr>{row_html}</tr>")
                    row_index += 1
                continue

            # Radio filter
            if not filter_radio:
                if (parsed.get("is_radio", False)
                    or "** [Kanał:" in line
                    or parsed["message"].lstrip().startswith("Audycja")):
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
            # If not recognized and user doesn't want unrecognized => skip
            if action not in self._formatter.ACTION_COLOR_MAP and not filter_unrecognized:
                continue

            # 'Show only related' logic:
            # lines with "Komenda" or is_radio are always shown
            def always_show(p: Dict[str, str]) -> bool:
                return p["action"] == "Komenda" or p.get("is_radio", False)

            combined_text = (parsed.get("prefix", "") + " " + parsed.get("message", "")).lower()
            matching_I = [nm.lower() for nm in selected_I if nm.lower() in combined_text]
            matching_O = [nm.lower() for nm in selected_O if nm.lower() in combined_text]

            # Build the [I]/[I1]/[O]/[O2] tags unconditionally
            tag = ""
            if matching_I:
                if len(matching_I) == 1:
                    tag += "[I] "
                else:
                    for i, _ in enumerate(sorted(matching_I), start=1):
                        tag += f"[I{i}] "
            if matching_O:
                if len(matching_O) == 1:
                    tag += "[O] "
                else:
                    for i, _ in enumerate(sorted(matching_O), start=1):
                        tag += f"[O{i}] "
            # If 'show only related' is on, skip if no match
            if show_only_related and not always_show(parsed):
                if not matching_I and not matching_O:
                    continue

            # Build timestamp
            date_part = parsed.get("date", "")
            time_part = parsed.get("time", "")
            new_timestamp = ""
            if show_date and date_part:
                new_timestamp += date_part
            if show_hour and time_part:
                if new_timestamp:
                    new_timestamp += " "
                new_timestamp += time_part
            if new_timestamp:
                new_timestamp = f"[{new_timestamp}]"

            timestamp_html = f'<span style="color: #00BFFF; font-weight: bold;">{new_timestamp}</span>'
            action_color = self._formatter.ACTION_COLOR_MAP.get(action, self._formatter.ACTION_COLOR_MAP["default"])
            action_html = f'<span style="color: {action_color}; font-weight: bold;">[{action}]</span>'

            prefix_html = ""
            if parsed.get("prefix"):
                prefix_html = f'<span style="color: #FFFFFF; font-weight: bold;">{parsed["prefix"]} </span>'

            message_html = f'<span style="color: #CCCCCC;">{parsed["message"]}</span>'

            tag_html = ""
            if tag:
                tag_html = f'<span style="color: #FF69B4; font-weight: bold;">{tag}</span> '

            log_line_html = " ".join([
                timestamp_html,
                action_html,
                tag_html,
                prefix_html,
                message_html
            ])

            row_html = (
                f"<td style='text-align: right; padding: 2px 5px; vertical-align: top;'>{row_index}</td>"
                f"<td style='padding: 2px 5px;'>{log_line_html}</td>"
            )
            table_rows.append(f"<tr>{row_html}</tr>")
            row_index += 1

        table_html = "<table style='width: 100%; border-collapse: collapse;'>" \
                     + "".join(table_rows) + "</table>"
        self._text_edit.setHtml(table_html)
