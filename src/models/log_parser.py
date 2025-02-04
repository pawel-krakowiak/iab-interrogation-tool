import re
from typing import List, Set


class LogParser:
    """Handles parsing of log files, extracting messages and unique users."""

    def __init__(self, file_path: str):
        """Initialize LogParser with a file path.

        Args:
            file_path (str): Path to the log file.
        """
        self.file_path = file_path
        self.logs: List[str] = []
        self.users: Set[str] = set()
        self.load_logs()

    def load_logs(self) -> None:
        """Loads logs from the file and extracts unique users."""
        with open(self.file_path, "r", encoding="utf-8") as file:
            for line in file:
                self.logs.append(line.strip())
                match = re.search(r"(\w+ \w+) mówi:", line)
                if match:
                    self.users.add(match.group(1))

    def get_sorted_logs(self, asc: bool = True) -> List[str]:
        """Returns logs sorted by date.

        Args:
            asc (bool): Sort order (True for ascending, False for descending).

        Returns:
            List[str]: Sorted log entries.
        """
        return sorted(self.logs, reverse=not asc)
