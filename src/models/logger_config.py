import logging
from logging import Logger


def setup_logger() -> Logger:
    logger = logging.getLogger("LogParserApp")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



logger = setup_logger()
