"""
Module log_formatter
====================

This module provides a LogFormatter class for parsing and formatting log lines.
Each log line is expected to follow the format:
    [Timestamp] [Action] [Content]

For example:
    [2.02.2025 22:19:38] [Czat IC] Howard Goldberg mówi: Na glebe skurwysynu ręce na głowe szeroko nogi.
    [2.02.2025 22:19:35] [Akcja /me] * Nieznajomy JCZAK wskazała na Musaeva, spojrzała na Walsh'a.

The formatter splits each log line into:
    - timestamp (with separate date and time parts)
    - action (and if possible, a name if it follows a pattern such as "NAME mówi:" or "NAME szepcze:" etc.)
    - message (the remaining text)

The formatted output is returned as an HTML string, with inline CSS styles for syntax highlighting.
"""

import re
from datetime import datetime
from typing import Optional, Dict

# Mapping of action types to their display colors (you can extend this mapping as needed)
ACTION_COLOR_MAP = {
    "Czat IC": "#FFD700",  # Gold
    "Czat OOC": "#FF8C00",  # Dark Orange
    "Akcja /me": "#ADFF2F",  # GreenYellow
    "Akcja /do": "#00CED1",  # DarkTurquoise
    "Komenda": "#FF4500",  # OrangeRed
    "PW": "#DA70D6",  # Orchid
    # Default color if action type is not recognized
    "default": "#FFFFFF",  # White
}


class LogFormatter:
    """A class to parse and format log lines with syntax highlighting."""

    # Regular expression to capture the basic three parts of a log line.
    # Assumes format: [Timestamp] [Action] [Content]
    LOG_PATTERN = re.compile(
        r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<action>[^\]]+)\]\s+(?P<message>.*)$"
    )

    # Regular expression to extract the speaker's name and tone.
    # This pattern recognizes lines where the message starts with:
    # "Name mówi:", "Name szepcze:", "Name krzyczy:" or "Name szepcze do Other:".
    NAME_PATTERN = re.compile(
        r"^(?P<name>[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)\s+(?P<tone>mówi|szepcze|krzyczy)(\s+do\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)?:"
    )

    def parse_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parses a log line into its components.

        Args:
            line (str): A single log line.

        Returns:
            Optional[Dict[str, str]]: A dictionary containing:
                - 'timestamp': the original timestamp string,
                - 'date': parsed date in YYYY-MM-DD format,
                - 'time': parsed time in HH:MM:SS format,
                - 'action': the action string,
                - 'name': the extracted name if found (empty string otherwise),
                - 'message': the log message text.
            Returns None if the line does not match the expected format.
        """
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None

        timestamp_str = match.group("timestamp")
        action = match.group("action").strip()
        message = match.group("message").strip()

        # Attempt to parse the timestamp; expected format is like "2.02.2025 22:19:38"
        try:
            dt = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
        except ValueError:
            date_str = ""
            time_str = ""

        # Extract name and tone from the message if possible
        name = ""
        name_match = self.NAME_PATTERN.match(message)
        if name_match:
            name = name_match.group("name").strip()

        return {
            "timestamp": timestamp_str,
            "date": date_str,
            "time": time_str,
            "action": action,
            "name": name,
            "message": message,
        }

    def format_line(self, line: str) -> str:
        """Formats a single log line into an HTML string with syntax highlighting.

        The returned HTML highlights:
            - Timestamp (date/time) in a cool blue.
            - Action in a color based on its type.
            - Name (if available) in bold white.
            - The rest of the message in default text color.

        Args:
            line (str): A single log line.

        Returns:
            str: An HTML-formatted string.
        """
        parsed = self.parse_line(line)
        if not parsed:
            # If parsing fails, return the original line in a preformatted block.
            return f"<pre>{line}</pre>"

        # Colors
        timestamp_color = "#00BFFF"  # DeepSkyBlue
        action_color = ACTION_COLOR_MAP.get(
            parsed["action"], ACTION_COLOR_MAP["default"]
        )
        name_color = "#FFFFFF"  # White
        message_color = "#CCCCCC"  # Light gray

        # HTML formatted parts
        html_parts = []

        # Timestamp (date and time)
        html_parts.append(
            f'<span style="color: {timestamp_color}; font-weight: bold;">'
            f'[{parsed["timestamp"]}]'
            f"</span> "
        )

        # Action
        html_parts.append(
            f'<span style="color: {action_color}; font-weight: bold;">'
            f'[{parsed["action"]}]'
            f"</span> "
        )

        # Optionally, display name if extracted
        if parsed["name"]:
            html_parts.append(
                f'<span style="color: {name_color}; font-weight: bold;">'
                f'{parsed["name"]} '
                f"</span>"
            )

        # Message (the full message; if a name was extracted, you might want to remove it from the message, but here we keep it)
        html_parts.append(
            f'<span style="color: {message_color};">' f'{parsed["message"]}' f"</span>"
        )

        # Combine parts
        return "".join(html_parts)
