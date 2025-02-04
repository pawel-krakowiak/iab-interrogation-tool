import re
from datetime import datetime

import pytest
from src.models.log_formatter import LogFormatter, ACTION_COLOR_MAP

# Sample log lines for testing
LOG_LINE_MOWI = (
    "[2.02.2025 22:19:38] [Czat IC] Lilianna Anderson mówi: Kieszeń z tyłu spodni."
)
LOG_LINE_SZEPCZE = "[2.02.2025 22:20:48] [Czat IC] Nieznajomy ERLYW szepcze: Hahahaha."
LOG_LINE_KRZYCZY = "[2.02.2025 22:09:11] [Czat IC] Bernard Patton krzyczy: MORDA PHIL!"
LOG_LINE_SZEPCZE_DO = "[2.02.2025 22:20:44] [Czat IC] Nieznajomy BL8A szepcze do C Z: Nie szperaj po barze - a jak już bierzesz to bierz drogie."
LOG_LINE_NO_MATCH = "This is not a valid log line"


@pytest.fixture
def formatter() -> LogFormatter:
    """Fixture returning a LogFormatter instance."""
    return LogFormatter()


def test_parse_line_mowi(formatter: LogFormatter):
    """Test parsing a log line with 'mówi:'."""
    result = formatter.parse_line(LOG_LINE_MOWI)
    assert result is not None, "Parsing should succeed"

    # Check timestamp parsing
    expected_dt = datetime.strptime("2.02.2025 22:19:38", "%d.%m.%Y %H:%M:%S")
    assert result["date"] == expected_dt.strftime("%Y-%m-%d")
    assert result["time"] == expected_dt.strftime("%H:%M:%S")

    # Check action
    assert result["action"] == "Czat IC"

    # Check name extraction
    # Expecting "Lilianna Anderson" to be extracted
    assert result["name"] == "Lilianna Anderson"

    # Check message contains the original text
    assert "Kieszeń" in result["message"]


def test_parse_line_szepcze(formatter: LogFormatter):
    """Test parsing a log line with 'szepcze:'."""
    result = formatter.parse_line(LOG_LINE_SZEPCZE)
    assert result is not None, "Parsing should succeed"
    assert result["action"] == "Czat IC"
    # Expecting "Nieznajomy ERLYW" to be extracted
    assert result["name"] == "Nieznajomy ERLYW"
    assert "Hahahaha" in result["message"]


def test_parse_line_krzyczy(formatter: LogFormatter):
    """Test parsing a log line with 'krzyczy:'."""
    result = formatter.parse_line(LOG_LINE_KRZYCZY)
    assert result is not None, "Parsing should succeed"
    assert result["action"] == "Czat IC"
    # Expecting "Bernard Patton" to be extracted
    assert result["name"] == "Bernard Patton"
    assert "MORDA PHIL" in result["message"]


def test_parse_line_szepcze_do(formatter: LogFormatter):
    """Test parsing a log line with 'szepcze do'."""
    result = formatter.parse_line(LOG_LINE_SZEPCZE_DO)
    assert result is not None, "Parsing should succeed"
    assert result["action"] == "Czat IC"
    # Expecting "Nieznajomy BL8A" to be extracted as name (ignoring the 'do C Z' part for now)"
    assert result["name"] == "Nieznajomy BL8A"
    assert "Nie szperaj po barze" in result["message"]


def test_parse_line_invalid(formatter: LogFormatter):
    """Test that an invalid log line returns None."""
    result = formatter.parse_line(LOG_LINE_NO_MATCH)
    assert result is None


def test_format_line_contains_html(formatter: LogFormatter):
    """Test that format_line returns an HTML string with expected elements."""
    html = formatter.format_line(LOG_LINE_MOWI)
    # Check that timestamp is wrapped in a span with DeepSkyBlue color (#00BFFF)
    assert "color: #00BFFF" in html
    # Check that action is wrapped with the correct color for "Czat IC"
    expected_action_color = ACTION_COLOR_MAP.get("Czat IC", ACTION_COLOR_MAP["default"])
    assert f"color: {expected_action_color}" in html
    # Check that the name "Lilianna Anderson" is present
    assert "Lilianna Anderson" in html
    # Check that the message content appears in the HTML
    assert "Kieszeń" in html


def test_format_line_invalid(formatter: LogFormatter):
    """Test that an invalid log line is returned as a preformatted block."""
    html = formatter.format_line(LOG_LINE_NO_MATCH)
    # Should wrap the original line in a <pre> tag
    assert html.startswith("<pre>")
    assert html.endswith("</pre>")
