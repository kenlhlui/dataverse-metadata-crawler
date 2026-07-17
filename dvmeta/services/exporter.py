"""ExportManager class for managing JSON exports with descriptions and tracking."""

from pathlib import Path

import orjson
from loguru import logger

from dvmeta.services.dir_manager import DirManager
from dvmeta.services.dir_manager import ExportDir
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import gen_checksum


class ExportManager:
    """Class to manage JSON exports with predefined descriptions and tracking."""

    # Preset descriptions for different export types
    DESCRIPTIONS = {
        'pid_dict_dd': 'Hierarchical Information of Datasets(deaccessioned/draft)',
        'failed_metadata_uris': 'PIDs of Datasets Failed to be crawled (Representation & File)',
        'permission_dict': 'Dataset Metadata (Permission)',
        'pid_dict': 'Hierarchical Information of Datasets',
        'ds_metadata': 'Dataset Metadata (Representation, File & Permission)',
        'empty_dv': 'Empty Dataverses',
        'spreadsheet': 'Dataset Metadata CSV',
    }

    def __init__(self) -> None:
        """Initialize the export manager."""
        self.tracking_nested_list = []

    def export(self, data: dict, export_type: str) -> tuple[Path | None, str | None]:
        """Export data to JSON and log the information.

        Args:
            data: The data to export
            export_type: Type identifier (used as filename and for preset description)

        Returns:
            Tuple of (json_path, checksum) from the export operation
        """
        # Get description from presets or use custom if provided
        description = self.DESCRIPTIONS.get(export_type, f'Export of {export_type}')

        # Get the JSON DIR
        json_dir = DirManager().get_dir(ExportDir.JSON)

        # Get the json file path with timestamp
        json_file_path = Path(json_dir, f'{export_type}_{get_file_timestamp()}.json')

        # Export the file if data is a non-empty dictionary
        if isinstance(data, dict) and data:
            Path(json_dir).mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
            json_file_path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
            checksum = gen_checksum(json_file_path)
            logger.info(
                f'Exported {json_file_path.name} to json file: {json_file_path}\nChecksum (SHA-256): {checksum}'
            )

            # Log the export if tracking is enabled
            if self.tracking_nested_list is not None:
                self.tracking_nested_list.append({
                    'type': description,
                    'path': json_file_path,
                    'checksum': checksum,
                })

            return json_file_path, checksum
        logger.info(f'{json_file_path.name} is empty, no json file is created.')
        return None, None
