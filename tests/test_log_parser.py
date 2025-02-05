import pytest
from pathlib import Path
from src.models.log_parser import LogParser


@pytest.fixture
def sample_log_file(tmp_path: Path) -> str:
    """
    Creates a temporary log file with sample content and returns its path.
    """
    log_content = (
        "[2.02.2025 22:19:38] [Czat IC] John Doe mówi: Hello world!\n"
        "[2.02.2025 22:20:48] [Czat IC] Jane Smith mówi: Hi there!\n"
        "Invalid log line\n"
    )
    log_file = tmp_path / "sample_log.txt"
    log_file.write_text(log_content, encoding="utf-8")
    return str(log_file)


def test_load_logs(sample_log_file: str) -> None:
    """
    Test that LogParser loads all lines from the file and extracts unique
    users.
    """
    parser = LogParser(sample_log_file)
    # There are three lines in the file.
    assert len(parser.logs) == 3
    # Should extract "John Doe" and "Jane Smith" as unique users.
    assert "John Doe" in parser.users
    assert "Jane Smith" in parser.users
