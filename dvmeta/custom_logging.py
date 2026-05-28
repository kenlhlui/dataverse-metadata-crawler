"""This module defines a custom logger for the package."""

# ruff: noqa: ANN401
import logging
from pathlib import Path

from loguru import logger


class CustomLogger:
    """Logger class that uses Loguru for logging."""

    @staticmethod
    def setup_logging(log_file_dir: Path | None = None, log_level: int = logging.INFO):
        """Setup logging configuration for Loguru."""
        # Remove existing handlers
        logger.remove()

        # Add the console log format with color
        console_log_format: str = '<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> - <level>{message}</level>'

        # Add the console handler
        logger.add(
            sink=lambda msg: print(msg, end=''),
            colorize=True,
            level=log_level,
            format=console_log_format,
        )

        # Add the file handler if log_file_dir is provided
        if log_file_dir:
            log_file_path = Path(log_file_dir, 'debug.log')
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                sink=str(log_file_path),
                level=logging.DEBUG,
                format='{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}',
                encoding='utf-8',
            )
