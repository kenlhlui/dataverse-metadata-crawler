"""This module defines a custom logger for the package."""

# ruff: noqa: ANN401
import logging
from pathlib import Path
from typing import Any

from loguru import logger


class LoguruLogger:
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

    @staticmethod
    def get_logger(name: str) -> 'CustomLoggerWrapper':
        """Get a logger with the specified name.

        Args:
            name: The name of the logger (typically __name__)

        Returns:
            CustomLoggerWrapper: A wrapper around the loguru logger
        """
        return CustomLoggerWrapper(logger.bind(name=name))


class CustomLoggerWrapper:
    """Wrapper around logger to provide clean interface."""

    def __init__(self, logger: Any) -> None:
        """Initialize the logger wrapper with a specific logger.

        Args:
            logger: Either a logging.Logger or loguru.Logger instance
        """
        self.logger = logger

    def print(self, message: Any) -> None:
        """Log a message with the custom PRINT level (maps to INFO in loguru)."""
        self.logger.info(message)

    def info(self, message: Any) -> None:
        """Log a message with INFO level."""
        self.logger.info(message)

    def warning(self, message: Any) -> None:
        """Log a message with WARNING level."""
        self.logger.warning(message)

    def error(self, message: Any) -> None:
        """Log a message with ERROR level."""
        self.logger.error(message)

    def critical(self, message: Any) -> None:
        """Log a message with CRITICAL level."""
        self.logger.critical(message)

    def debug(self, message: Any) -> None:
        """Log a message with DEBUG level."""
        self.logger.debug(message)


# Backward compatibility alias
CustomLogger = LoguruLogger
