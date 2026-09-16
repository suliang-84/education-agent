import sys

from loguru import logger


def setup_logger() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} - {message}",
        level="DEBUG",
        colorize=True,
    )
    logger.add(
        "logs/app.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO",
        encoding="utf-8",
    )
