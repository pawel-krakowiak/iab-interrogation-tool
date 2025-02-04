import logging


def setup_logger() -> logging.Logger:
    """Configures and returns the application logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("LogParserApp")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logger()
