import re
from typing import List, Set


class LogParser:
    """
    Handles parsing of log files, extracting messages and unique users.
    """

    USER_PATTERN = re.compile(r"(\w+ \w+) mówi:")

    def __init__(self, file_path: str) -> None:
        """
        Initialize LogParser with a file path.

        Args:
            file_path (str): Path to the log file.
        """
        self.file_path: str = file_path
        self.logs: List[str] = []
        self.users: Set[str] = set()
        self._load_logs()

    def _load_logs(self) -> None:
        """Loads logs from the file and extracts unique users."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                for line in file:
                    stripped_line = line.strip()
                    self.logs.append(stripped_line)
                    self._extract_user(stripped_line)
        except FileNotFoundError:
            raise ValueError(f"File not found: {self.file_path}")

    def _extract_user(self, line: str) -> None:
        """Extracts unique users from the log line."""
        match = self.USER_PATTERN.search(line)
        if match:
            self.users.add(match.group(1))

    def get_sorted_logs(self, ascending: bool = True) -> List[str]:
        """
        Returns logs sorted by date.

        Args:
            ascending (bool): True for ascending, False for descending.

        Returns:
            List[str]: Sorted log entries.
        """
        return sorted(self.logs, reverse=not ascending)
