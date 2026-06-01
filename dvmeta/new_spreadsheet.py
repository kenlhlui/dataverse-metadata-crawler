# ruff: noqa: PLR1733
"""A module to manage the creation of CSV files from metadata dictionaries."""

from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from loguru import logger

from dvmeta.csv_model import DatasetExportRow
from dvmeta.dirmanager import DirManager
from dvmeta.models import CitationAccessor
from dvmeta.models import Config
from dvmeta.models import DatasetData
from dvmeta.timestamp import get_file_timestamp
from dvmeta.utils import gen_checksum


# ruff: noqa: W293


class Spreadsheet:
    """A class to manage the creation of CSV files from metadata dictionaries."""

    def __init__(self, config: Config) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config

        self.csv_file_dir = DirManager().csv_files_dir()
        self.spreadsheet_order_file_path = Path(DirManager().res_dir) / 'spreadsheet_order.csv'

    @staticmethod
    def serialize_row(
        row: DatasetExportRow,
    ) -> dict:
        """Serialize export row."""
        result = {}

        for key, value in row.items():
            if isinstance(value, list):
                result[key] = '; '.join(str(item) for item in value)
            else:
                result[key] = value

        return result

    @staticmethod
    def _get_data_files_size(dictionary: dict) -> int | str:
        data = dictionary.get('data')
        if data is not None and 'files' in data:
            data_files_size_list: list = jmespath.search('data.files[*].dataFile.filesize|[]', dictionary)
            if data_files_size_list:
                return sum(data_files_size_list)
        return 'Error'

    @staticmethod
    def _get_data_files_count(dictionary: dict) -> int | str:
        data = dictionary.get('data')
        if data is not None and 'files' in data:
            data_files_count: int = len(jmespath.search('data.files', dictionary))
            return data_files_count
        return 'Error'

    @staticmethod
    def _get_restricted_data_files_count(dictionary: dict) -> int | str:
        data = dictionary.get('data')
        if data is not None and 'files' in data:
            data_files_count: list = jmespath.search('data.files[?restricted==`true`]', dictionary)
            return len(data_files_count) if data_files_count else 0
        return 'Error'

    @staticmethod
    def _get_dataset_path(dictionary: dict) -> str:
        path_info = dictionary.get('path_info')
        if path_info is not None and 'path' in path_info:
            return path_info.get('path')
        if path_info is None:
            return 'root'
        return 'Error'

    @staticmethod
    def _get_dataset_version(dictionary: dict) -> float | str:
        version_number = dictionary.get('versionNumber')
        version_minor_number = dictionary.get('versionMinorNumber')
        if version_number is not None and version_minor_number is not None:
            return float(f'{version_number}.{version_minor_number}')
        return 'Error'

    def _get_datafile_meta_usage(dictionary: dict) -> dict:
        # Get the use of data file directoryLabel (DF_Hierarchy),
        # tags (categories; DF_Tags) & description (DF_Description).
        if dictionary.get('data', {}).get('files'):
            file_nested_list = jmespath.search('data.files[*]', dictionary)

            # Get the count of directoryLabel if it is not None
            directorylabel_count = len([file for file in file_nested_list if file.get('directoryLabel') is not None])

            # Get the count of categories if it is not None
            categories_count = len(
                [file for file in file_nested_list if file.get('dataFile', {}).get('categories') is not None]
            )

            # Get the count of description if it is not None
            description_count = len(
                [file for file in file_nested_list if file.get('dataFile', {}).get('description') is not None]
            )

            return {
                'DF_Hierarchy': directorylabel_count,
                'DF_Tags': categories_count,
                'DF_Description': description_count,
            }
        return {'DF_Hierarchy': 0, 'DF_Tags': 0, 'DF_Description': 0}

    def make_csv_file(self, meta_dict: dict) -> tuple[Path, str]:
        """Create a CSV file from the nested metadata list.

        Args:
            meta_dict (dict): Dataset metadata dictionary

        Returns:
            tuple[Path, str]: Path to the CSV file, Checksum of the CSV file
        """
        # Create a DataFrame from the nested list

        # Create the CSV file
        csv_file_path = Path(self.csv_file_dir).joinpath(f'ds_metadata_{get_file_timestamp()}.csv')

        rows = []
        for _, dataset_meta in meta_dict.items():
            dataset = DatasetData.model_validate(dataset_meta['data'])
            if dataset.latestVersion is None:
                continue
            citation = CitationAccessor(
                dataset.latestVersion.metadataBlocks.citation,
            )
            row = DatasetExportRow(
                DatasetTitle=citation.get('title', ''),
                DatasetURL=urljoin(
                    self.config.base_url, f'/dataset.xhtml?persistentId={dataset.latestVersion.datasetPersistentId}'
                )
                if dataset.latestVersion.datasetPersistentId
                else '',
                DS_Path=dataset_meta.get('dataset_path', ''),
                ID=dataset.id,
                DatasetPersistentId=dataset.latestVersion.datasetPersistentId,
                DatasetId=dataset.datasetId,
                VersionState=dataset.latestVersion.versionState,
                LastUpdateTime=dataset.latestVersion.lastUpdateTime,
                ReleaseTime=dataset.latestVersion.releaseTime,
                CreateTime=dataset.latestVersion.createTime,
                FileCount='PH',
                FileSize='PH',
                FileSize_normalized='PH',
                License=citation.get('license', ''),
                RestrictedFiles='PH',
                TermsOfUse=citation.get('termsOfUse', ''),
                RequestAccess=citation.get('requestAccess', False),
                TermsAccess=citation.get('termsAccess', ''),
                DF_Hierarchy='PH',
                DF_Tags='PH',
                DF_Description='PH',
                CM_Subtitle=citation.get('subtitle', ''),
                CM_AltTitle=citation.get('alternativeTitle', []),
                CM_AltURL=citation.get('alternativeURL', ''),
                CM_Agency=citation.get('authority', []),
                CM_ID=citation.get('identifier', []),
                CM_NumberAuthors=len(citation.get('author', [])),
                CM_Author=citation.get('author', []),
                CM_AuthorAff=citation.get('authorAffiliation', []),
                CM_AuthorIDType=citation.get('authorIdentifierType', []),
                CM_AuthorID=citation.get('authorIdentifier', []),
                CM_ContactName=citation.get('contactName', []),
                CM_ContactAff=citation.get('contactAffiliation', []),
                CM_Descr=citation.get('description', []),
                CM_DescrDate=citation.get('descriptionDate', []),
                CM_Subject=citation.get('subject', []),
                CM_Subject_Agri=citation.get_compound_values('subject', 'agriculturalSubject'),
            )
            row_serialized = self.serialize_row(row)
            rows.append(row_serialized)

        # Turn the list of dictionaries into a DataFrame

        df = pd.DataFrame(rows)

        df.to_csv(csv_file_path, index=False)

        # Generate a checksum for the CSV file
        checksum = gen_checksum(csv_file_path)

        logger.info(f'Exported Dataset Metadata CSV: {csv_file_path}\nChecksum (SHA-256): {checksum}')

        return csv_file_path, checksum
