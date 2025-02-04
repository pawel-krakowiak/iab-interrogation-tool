"""
Module log_formatter
====================

This module provides a LogFormatter class for parsing and formatting log lines.
Each log line is expected to follow the format:
    [Timestamp] [Action] [Content]

For example:
    [2.02.2025 22:19:38] [Czat IC] Howard Goldberg mówi: Na glebe skurwysynu ręce na głowę szeroko nogi.
    [2.02.2025 22:19:35] [Akcja /me] * Nieznajomy JCZAK wskazała na Musaeva, spojrzała na Walsh'a.

The formatter splits each log line into:
    - timestamp (with separate date and time parts)
    - action
    - speaker prefix: the entire speaker part (e.g., "Lauren Devaughn mówi:")
    - message: the remaining log text
    - is_radio: a boolean indicating if the call is a radio call (when extra info "(radio)" is present)

The formatted output is returned as an HTML-formatted string with inline CSS styles.
"""

import re
from datetime import datetime
from typing import Optional, Dict, List

# Mapping of action types to their display colors.
ACTION_COLOR_MAP: Dict[str, str] = {
    "Czat IC": "#FFD700",  # Gold
    "Czat OOC": "#FF8C00",  # Dark Orange
    "Akcja /me": "#ADFF2F",  # GreenYellow
    "Akcja /do": "#00CED1",  # DarkTurquoise
    "Komenda": "#FF4500",  # OrangeRed
    "PW": "#DA70D6",  # Orchid
    "default": "#FFFFFF",  # White (default)
}


class LogFormatter:
    """A class to parse and format log lines with syntax highlighting."""

    # Regular expression to capture the basic three parts of a log line.
    LOG_PATTERN = re.compile(
        r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<action>[^\]]+)\]\s+(?P<message>.*)$"
    )

    # Regex to capture speaker prefix and optional extra info (e.g., (radio)).
    NAME_PATTERN = re.compile(
        r"^(?P<name>[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)\s+"
        r"(?P<tone>mówi|szepcze|krzyczy)"
        r"(?:\s*\((?P<extra>[^)]+)\))?"  # optional extra info (e.g., radio)
        r"(?:\s+do\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)?:\s*"
    )

    def parse_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Parses a log line into its components.

        Args:
            line (str): A single log line.

        Returns:
            Optional[Dict[str, str]]: Dictionary containing:
                - 'timestamp': original timestamp string.
                - 'date': date in YYYY-MM-DD format.
                - 'time': time in HH:MM:SS format.
                - 'action': the action string.
                - 'prefix': speaker prefix (if found).
                - 'message': log message with prefix removed.
                - 'is_radio': boolean flag (True if extra info equals "radio").
            Returns None if the line does not match the expected format.
        """
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None

        timestamp_str: str = match.group("timestamp")
        action: str = match.group("action").strip()
        message: str = match.group("message").strip()

        # Parse timestamp.
        try:
            dt = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M:%S")
            date_str: str = dt.strftime("%Y-%m-%d")
            time_str: str = dt.strftime("%H:%M:%S")
        except ValueError:
            date_str, time_str = "", ""

        prefix: str = ""
        is_radio: bool = False
        name_match = self.NAME_PATTERN.match(message)
        if name_match:
            prefix = name_match.group(0).strip()
            extra = name_match.group("extra")
            if extra and extra.lower() == "radio":
                is_radio = True
            # Remove the prefix from the message.
            message = message[len(prefix) :].strip()

        return {
            "timestamp": timestamp_str,
            "date": date_str,
            "time": time_str,
            "action": action,
            "prefix": prefix,
            "message": message,
            "is_radio": is_radio,
        }

    def format_line(self, line: str, index: int) -> str:
        """
        Formats a single log line into an HTML string with syntax highlighting.

        The HTML highlights:
            - Row index in gray.
            - Timestamp in DeepSkyBlue.
            - Action in its corresponding color.
            - Speaker prefix (if any) in bold white.
            - Message in light gray.

        Args:
            line (str): A single log line.
            index (int): The row number (starting at 1).

        Returns:
            str: An HTML-formatted string.
        """
        parsed = self.parse_line(line)
        if not parsed:
            return f"<pre>{index}: {line}</pre>"

        timestamp_color = "#00BFFF"  # DeepSkyBlue
        action_color: str = ACTION_COLOR_MAP.get(
            parsed["action"], ACTION_COLOR_MAP["default"]
        )
        prefix_color = "#FFFFFF"  # White
        message_color = "#CCCCCC"  # Light gray

        html_parts: List[str] = []
        html_parts.append(
            f'<span style="color: #AAAAAA; font-weight: bold;">[{index}]</span> '
        )
        html_parts.append(
            f'<span style="color: {timestamp_color}; font-weight: bold;">[{parsed["timestamp"]}]</span> '
        )
        html_parts.append(
            f'<span style="color: {action_color}; font-weight: bold;">[{parsed["action"]}]</span> '
        )
        if parsed.get("prefix"):
            html_parts.append(
                f'<span style="color: {prefix_color}; font-weight: bold;">{parsed["prefix"]} </span>'
            )
        html_parts.append(
            f'<span style="color: {message_color};">{parsed["message"]}</span>'
        )

        return "".join(html_parts)
