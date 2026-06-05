"""Module to manage the directories for exported files."""

from enum import StrEnum
from pathlib import Path

from loguru import logger


class ExportDir(StrEnum):
    """Enum to represent the different types of export directories."""

    JSON = 'json_files'
    LOG = 'log_files'
    CSV = 'csv_files'


class DirManager:
    """Class to manage directories and files in the data vault."""

    def __init__(self) -> None:
        """Initialize the class with the base directory for exported files."""
        self.export_base_dir = r'./exported_files'
        self.res_dir = r'./res'

    @staticmethod
    def _create_dir(path: Path) -> Path:
        """Helper method to create a directory if it doesn't exist.

        Args:
            path (Path): The path to the directory.

        Returns:
            Path: The path to the directory.
        """
        if not Path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.debug(f'Created directory: {path}')
        return path

    def get_dir(self, name: ExportDir) -> Path:
        """Get the directory path based on the provided name. Crate the directory if it doesn't exist.

        Args:
            name (ExportDir): The name of the directory to retrieve.

        Returns:
            Path: The path to the requested directory.
        """
        return self._create_dir(Path(self.export_base_dir) / name)
