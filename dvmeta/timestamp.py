"""This module contains a class to manage timestamps."""

# ruff: noqa: DTZ005
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Timestamps:
    """A dataclass to store start and end timestamps for the crawling process."""

    start_time: datetime
    end_time: datetime | None = None


def get_display_time(time_obj: datetime | None = None) -> str:
    """Returns a string representation of the time in the format: YYYY-MM-DD HH:MM:SS.

    Args:
        time_obj (datetime, optional): Time to format. Defaults to current time.

    Returns:
        str: A string representation of the time.
    """
    if time_obj is None:
        time_obj = datetime.now()
    return time_obj.strftime('%Y-%m-%d %H:%M:%S')


def get_file_timestamp() -> str:
    """Returns a string representation of the current time in the format: YYYYMMDD-HHMMSS.

    Returns:
        str: A string representation of the current time for use in file names
    """
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def get_current_time() -> datetime:
    """Returns the current time as a datetime object.

    Returns:
        datetime: The current time.
    """
    return datetime.now()


def get_elapsed_time(start_time: datetime, end_time: datetime | None = None) -> str:
    """Returns the elapsed time since the start time.

    Returns:
        str: The elapsed time in seconds.
    """
    end = end_time if end_time else datetime.now()
    elapsed_time = end - start_time
    return str(elapsed_time)
