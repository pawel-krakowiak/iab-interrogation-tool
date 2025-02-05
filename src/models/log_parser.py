"""
src/models/log_parser.py

Loads raw log lines from a file, extracts unique users, and provides sorted logs.
"""

import os
import re
import logging
from typing import List, Set, Dict

logger = logging.getLogger(__name__)


class LogParser:
    """
    Parses a log file, storing all lines and detecting unique users by pattern.
    """

    USER_PATTERN = re.compile(r"([\w\s\-]+?)\s+mówi(?:\s+\(([^)]+)\))?:")

    def __init__(self, file_path: str) -> None:
        """
        Args:
            file_path (str): The path to a log file.
        """
        self.file_path: str = file_path
        self.logs: List[str] = []
        self.users: Set[str] = set()
        self.user_frequencies: Dict[str, int] = {}
        self._load_logs()

    def _load_logs(self) -> None:
        """Loads logs from the file and extracts unique users."""
        if not os.path.isfile(self.file_path):
            logger.error(f"File not found: {self.file_path}")
            raise FileNotFoundError(f"File not found: {self.file_path}")

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                for line in file:
                    self.logs.append(line.strip())
                    self._extract_user(line)
        except OSError as e:
            logger.error(f"Error loading file {self.file_path}: {e}")
            raise

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
