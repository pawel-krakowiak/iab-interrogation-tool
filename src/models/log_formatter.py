"""
src/models/log_formatter.py

Provides a LogFormatter class for parsing and formatting log lines with
syntax highlighting and optional radio detection.
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

ACTION_COLOR_MAP: Dict[str, str] = {
        "Czat IC": "#FFD700",  # Gold
        "Czat OOC": "#FF8C00",  # Dark Orange
        "Akcja /me": "#ADFF2F",  # GreenYellow
        "Akcja /do": "#00CED1",  # DarkTurquoise
        "Komenda": "#FF4500",  # OrangeRed
        "PW": "#DA70D6",  # Orchid
        "default": "#FFFFFF",  # Fallback
    }


class LogFormatter:
    """Parses and formats log lines into HTML or structured data."""

    ACTION_COLOR_MAP: Dict[str, str] = {
        "Czat IC": "#FFD700",  # Gold
        "Czat OOC": "#FF8C00",  # Dark Orange
        "Akcja /me": "#ADFF2F",  # GreenYellow
        "Akcja /do": "#00CED1",  # DarkTurquoise
        "Komenda": "#FF4500",  # OrangeRed
        "PW": "#DA70D6",  # Orchid
        "default": "#FFFFFF",  # Fallback
    }

    LOG_PATTERN = re.compile(
        r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<action>[^\]]+)\]\s+(?P<message>.*)$"
    )

    NAME_PATTERN = re.compile(
        r"^(?P<name>[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)\s+"
        r"(?P<tone>mówi|szepcze|krzyczy)"
        r"(?:\s*\((?P<extra>[^)]+)\))?"  # e.g., (radio)
        r"(?:\s+do\s+[A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-\']+?)?:\s*"
    )

    def parse_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Parses a single log line into structured data.
        Returns None if the format does not match LOG_PATTERN.
        """
        match = self.LOG_PATTERN.match(line)
        if not match:
            logger.debug("No match for LOG_PATTERN: %s", line)
            return {}


        timestamp_str = match.group("timestamp")
        action = match.group("action").strip()
        message = match.group("message").strip()

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

    def _parse_timestamp(self, timestamp: str) -> Tuple[str, str]:
        """
        Parses a timestamp string into date (YYYY-MM-DD) and time (HH:MM:SS).
        Returns empty strings if parsing fails.
        """
        try:
            dt = datetime.strptime(timestamp, "%d.%m.%Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
        except ValueError:
            logger.warning("Failed to parse timestamp: %s", timestamp)
            return "", ""

    def _extract_speaker_info(self, message: str) -> Tuple[str, bool, str]:
        """
        Extracts speaker prefix from the message and detects if it's a radio call.
        Returns (prefix, is_radio, new_message).
        """
        match = self.NAME_PATTERN.match(message)
        if not match:
            return "", False, message
        prefix = match.group(0).strip()
        extra = match.group("extra") or ""
        is_radio = extra.lower() == "radio"
        new_message = message[len(prefix) :].strip()
        return prefix, is_radio, new_message

    def format_line(self, line: str, index: int) -> str:
        """
        Formats a single log line into an HTML snippet with syntax highlighting.
        Returns a <pre> block if parsing fails.
        """
        parsed = self.parse_line(line)
        if not parsed:
            logger.debug("Line %d unrecognized format: %s", index, line)
            return f"<pre>{index}: {line}</pre>"

        timestamp_color = "#00BFFF"
        action_color = self.ACTION_COLOR_MAP.get(
            parsed["action"], self.ACTION_COLOR_MAP["default"]
        )
        prefix_color = "#FFFFFF"
        message_color = "#CCCCCC"

        return (
            f'<span style="color: #AAAAAA; font-weight: bold;">[{index}]</span> '
            f'<span style="color: {timestamp_color}; font-weight: bold;">[{parsed["timestamp"]}]</span> '
            f'<span style="color: {action_color}; font-weight: bold;">[{parsed["action"]}]</span> '
            f'<span style="color: {prefix_color}; font-weight: bold;">{parsed["prefix"]} </span>'
            f'<span style="color: {message_color};">{parsed["message"]}</span>'
        )
