"""
src/models/log_parser.py

Loads raw log lines from a file, extracts unique users, and provides sorted logs.
"""

import os
import re
import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class LogParser:
    """
    Parses a log file, storing all lines and detecting unique users by pattern.
    """

    USER_PATTERN = re.compile(r"(\w+ \w+) mówi:")

    def __init__(self, file_path: str) -> None:
        """
        Args:
            file_path (str): The path to a log file.
        """
        self.file_path: str = file_path
        self.logs: List[str] = []
        self.users: Set[str] = set()
        self._load_logs()

    def _load_logs(self) -> None:
        """Loads logs from the file and extracts unique users."""
        if not os.path.isfile(self.file_path):
            logger.error("File not found: %s", self.file_path)
            raise ValueError(f"File not found: {self.file_path}")

        logger.info("Loading logs from %s", self.file_path)
        with open(self.file_path, "r", encoding="utf-8") as file:
            for line in file:
                stripped_line = line.strip()
                self.logs.append(stripped_line)
                self._extract_user(stripped_line)

    def _extract_user(self, line: str) -> None:
        """Extracts unique users from a line based on USER_PATTERN."""
        match = self.USER_PATTERN.search(line)
        if match:
            self.users.add(match.group(1))

    def get_sorted_logs(self, ascending: bool = True) -> List[str]:
        """
        Returns logs sorted alphabetically or by date (expand as needed).
        """
        return sorted(self.logs, reverse=not ascending)
