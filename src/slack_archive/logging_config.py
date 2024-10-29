import logging
import sys

from slack_archive.config import LOG_FILE, LOG_LEVEL


def setup_logging(level: int = LOG_LEVEL) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        level: The logging level to use. Defaults to LOG_LEVEL from config.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Use 'w' mode to overwrite the file each time
    file_handler = logging.FileHandler(LOG_FILE, mode="w")
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Clear any existing handlers to avoid duplication
    logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
