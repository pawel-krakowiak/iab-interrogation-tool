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
from typing import Optional, Dict

class LogFormatter:
    """A class to parse and format log lines with syntax highlighting."""

    LOG_PATTERN = re.compile(
        r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<action>[^\]]+)\]\s+(?P<message>.*)$"
    )

    NAME_PATTERN = re.compile(
        r"^(?P<name>[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)\s+"
        r"(?P<tone>mówi|szepcze|krzyczy)"
        r"(?:\s*\((?P<extra>[^)]+)\))?"  # optional extra info (e.g., radio)
        r"(?:\s+do\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)?:\s*"
    )

    ACTION_COLOR_MAP: Dict[str, str] = {
        "Czat IC": "#FFD700",  # Gold
        "Czat OOC": "#FF8C00",  # Dark Orange
        "Akcja /me": "#ADFF2F",  # GreenYellow
        "Akcja /do": "#00CED1",  # DarkTurquoise
        "Komenda": "#FF4500",   # OrangeRed
        "PW": "#DA70D6",        # Orchid
        "default": "#FFFFFF",   # White (default)
    }

    def parse_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parses a log line into its components."""
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None

        timestamp_str, action, message = match.group("timestamp"), match.group("action").strip(), match.group("message").strip()
        date_str, time_str = self._parse_timestamp(timestamp_str)
        prefix, is_radio, message = self._extract_speaker_info(message)

        return {
            "timestamp": timestamp_str,
            "date": date_str,
            "time": time_str,
            "action": action,
            "prefix": prefix,
            "message": message,
            "is_radio": is_radio,
        }

    def _parse_timestamp(self, timestamp: str) -> (str, str):
        """Parses a timestamp string into date and time."""
        try:
            dt = datetime.strptime(timestamp, "%d.%m.%Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
        except ValueError:
            return "", ""

    def _extract_speaker_info(self, message: str) -> (str, bool, str):
        """Extracts speaker prefix and determines if the message is from radio."""
        match = self.NAME_PATTERN.match(message)
        if not match:
            return "", False, message

        prefix = match.group(0).strip()
        is_radio = match.group("extra") and match.group("extra").lower() == "radio"
        return prefix, is_radio, message[len(prefix):].strip()

    def format_line(self, line: str, index: int) -> str:
        """Formats a single log line into an HTML string with syntax highlighting."""
        parsed = self.parse_line(line)
        if not parsed:
            return f"<pre>{index}: {line}</pre>"

        timestamp_color = "#00BFFF"  # DeepSkyBlue
        action_color = self.ACTION_COLOR_MAP.get(parsed["action"], self.ACTION_COLOR_MAP["default"])
        prefix_color = "#FFFFFF"       # White
        message_color = "#CCCCCC"      # Light gray

        return (
            f'<span style="color: #AAAAAA; font-weight: bold;">[{index}]</span> '
            f'<span style="color: {timestamp_color}; font-weight: bold;">[{parsed["timestamp"]}]</span> '
            f'<span style="color: {action_color}; font-weight: bold;">[{parsed["action"]}]</span> '
            f'<span style="color: {prefix_color}; font-weight: bold;">{parsed["prefix"]} </span>'
            f'<span style="color: {message_color};">{parsed["message"]}</span>'
        )
