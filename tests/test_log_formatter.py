import pytest
from src.models.log_formatter import LogFormatter, ACTION_COLOR_MAP


@pytest.fixture
def formatter() -> LogFormatter:
    """Fixture returning a LogFormatter instance."""
    return LogFormatter()


def test_parse_line_normal(formatter: LogFormatter) -> None:
    """
    Test parsing a normal log line (non-radio).
    Expected to extract timestamp, action, prefix and message correctly.
    """
    line = "[2.02.2025 22:19:38] [Czat IC] Howard Goldberg mówi: Na glebe skurwysynu ręce na głowę szeroko nogi."
    result = formatter.parse_line(line)
    assert result is not None
    assert result["timestamp"] == "2.02.2025 22:19:38"
    # Expected prefix and message.
    assert result["prefix"] == "Howard Goldberg mówi:"
    assert result["message"] == "Na glebe skurwysynu ręce na głowę szeroko nogi."
    assert result["is_radio"] is False


def test_parse_line_radio(formatter: LogFormatter) -> None:
    """
    Test parsing a radio call log line.
    Expected to flag the line as radio and extract prefix and message.
    """
    line = "[2.02.2025 22:20:48] [Czat IC] John Doe mówi (radio): This is a radio call."
    result = formatter.parse_line(line)
    assert result is not None
    # The prefix should include "(radio)" and is_radio should be True.
    assert "John Doe mówi" in result["prefix"]
    assert result["is_radio"] is True
    assert result["message"] == "This is a radio call."


def test_parse_line_invalid(formatter: LogFormatter) -> None:
    """
    Test that an invalid log line (not matching the pattern) returns None.
    """
    line = "This is not a valid log line."
    result = formatter.parse_line(line)
    assert result is None


def test_format_line_html_structure(formatter: LogFormatter) -> None:
    """
    Test that format_line returns an HTML string that includes:
      - The row index.
      - The timestamp.
      - The action.
      - The speaker prefix.
      - The message.
    """
    line = "[2.02.2025 22:19:38] [Czat IC] Jane Smith mówi: Hello world!"
    formatted = formatter.format_line(line, 1)
    # Check for index and other components.
    assert "[1]" in formatted
    assert "[2.02.2025 22:19:38]" in formatted
    assert "[Czat IC]" in formatted
    assert "Jane Smith mówi:" in formatted
    assert "Hello world!" in formatted


def test_format_line_non_matching(formatter: LogFormatter) -> None:
    """
    If the log line doesn't match the expected pattern,
    format_line should return it wrapped in a <pre> tag.
    """
    line = "Invalid log line that doesn't match format"
    formatted = formatter.format_line(line, 1)
    assert formatted.startswith("<pre>")
    assert "Invalid log line" in formatted
