"""Utility functions for dvmeta CLI."""

from contextlib import contextmanager

from rich.progress import Progress
from rich.progress import SpinnerColumn


@contextmanager
def spinner():
    with Progress(SpinnerColumn(), transient=True) as progress:
        progress.add_task('', total=None)
        yield
