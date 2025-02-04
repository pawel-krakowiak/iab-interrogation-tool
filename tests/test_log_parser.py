from src.models.log_parser import LogParser


def test_load_logs():
    """Tests whether logs load correctly from a sample file."""
    parser = LogParser("tests/sample_logs2.txt")
    assert len(parser.logs) > 0
    assert isinstance(parser.users, set)


def test_get_sorted_logs():
    """Tests sorting functionality of the log parser."""
    parser = LogParser("tests/sample_logs2.txt")
    sorted_logs = parser.get_sorted_logs(asc=True)
    assert sorted_logs == sorted(parser.logs)
