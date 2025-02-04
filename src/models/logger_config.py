import logging
from logging import Logger

def setup_logger() -> Logger:
    """Configures and returns the application logger.

    Returns:
        Logger: A logger configured to write debug messages to 'logs/app.log'.
    """
    logger = logging.getLogger("LogParserApp")
    logger.setLevel(logging.DEBUG)
    # Create file handler which logs even debug messages.
    handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger()
