# ruff: noqa: PLR1733
"""A module to manage the creation of CSV files from metadata dictionaries."""

from pathlib import Path
from urllib.parse import urljoin

import jmespath
import pandas as pd
from loguru import logger

from dvmeta.models.config import Config
from dvmeta.models.csv_model import DatasetExportRow
from dvmeta.models.models import CitationAccessor
from dvmeta.models.models import DatasetData
from dvmeta.services.dir_manager import DirManager
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import convert_size
from dvmeta.services.utils import gen_checksum


class Spreadsheet:
    """A class to manage the creation of CSV files from metadata dictionaries."""

    def __init__(self, config: Config) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config
        self.csv_file_dir = DirManager().csv_files_dir()
        self.spreadsheet_order_file_path = Path(DirManager().res_dir) / 'spreadsheet_order.csv'

    @staticmethod
    def serialize_row(row: DatasetExportRow) -> dict:
        """Serialize export row, joining lists into '; '-separated strings."""
        result = {}
        for key, value in row.items():
            if isinstance(value, list):
                result[key] = '; '.join(str(item) for item in value if item is not None)
            else:
                result[key] = value
        return result

    @staticmethod
    def _get_data_files_size(dictionary: dict) -> int | str:
        latest_version = dictionary.get('data', {}).get('latestVersion', {})
        if 'files' in latest_version:
            data_files_size_list: list = jmespath.search('data.latestVersion.files[*].dataFile.filesize|[]', dictionary)
            if data_files_size_list:
                return sum(data_files_size_list)
        return 'Error'

    @staticmethod
    def _get_data_files_count(dictionary: dict) -> int | str:
        latest_version = dictionary.get('data', {}).get('latestVersion', {})
        if 'files' in latest_version:
            return len(jmespath.search('data.latestVersion.files', dictionary))
        return 'Error'

    @staticmethod
    def _get_restricted_data_files_count(dictionary: dict) -> int | str:
        latest_version = dictionary.get('data', {}).get('latestVersion', {})
        if 'files' in latest_version:
            data_files_count: list = jmespath.search('data.latestVersion.files[?restricted==`true`]', dictionary)
            return len(data_files_count) if data_files_count else 0
        return 'Error'

    @staticmethod
    def _get_datafile_meta_usage(dictionary: dict) -> dict:
        if dictionary.get('data', {}).get('latestVersion', {}).get('files'):
            file_nested_list = jmespath.search('data.latestVersion.files[*]', dictionary)
            directorylabel_count = len([f for f in file_nested_list if f.get('directoryLabel') is not None])
            categories_count = len([f for f in file_nested_list if f.get('dataFile', {}).get('categories') is not None])
            description_count = len(
                [f for f in file_nested_list if f.get('dataFile', {}).get('description') is not None]
            )
            return {
                'DF_Hierarchy': directorylabel_count,
                'DF_Tags': categories_count,
                'DF_Description': description_count,
            }
        return {'DF_Hierarchy': 0, 'DF_Tags': 0, 'DF_Description': 0}

    @staticmethod
    def _get_dataset_version(dataset_meta: dict) -> float | str:
        latest_version = dataset_meta.get('data', {}).get('latestVersion', {})
        version_number = latest_version.get('versionNumber')
        version_minor_number = latest_version.get('versionMinorNumber')
        if version_number is not None and version_minor_number is not None:
            return float(f'{version_number}.{version_minor_number}')
        return 'Error'

    @staticmethod
    def _get_dataset_subjects(subject_list: list) -> dict:
        subject_map = {
            'CM_Subject_Agri': 'Agricultural Sciences',
            'CM_Subject_AH': 'Arts and Humanities',
            'CM_Subject_Astro': 'Astronomy and Astrophysics',
            'CM_Subject_BM': 'Business and Management',
            'CM_Subject_Chem': 'Chemistry',
            'CM_Subject_Comp': 'Computer and Information Science',
            'CM_Subject_EES': 'Earth and Environmental Sciences',
            'CM_Subject_Eng': 'Engineering',
            'CM_Subject_Law': 'Law',
            'CM_Subject_Math': 'Mathematical Sciences',
            'CM_Subject_Med': 'Medicine, Health and Life Sciences',
            'CM_Subject_Phys': 'Physics',
            'CM_Subject_SocSci': 'Social Sciences',
            'CM_Subject_Other': 'Other',
        }
        if subject_list:
            return {key: value in subject_list for key, value in subject_map.items()}
        return dict.fromkeys(subject_map, False)

    @staticmethod
    def _get_metadata_blocks_usage(dataset_meta: dict) -> dict:
        metadata_block_map = {
            'Meta_Geo': 'geospatial',
            'Meta_SSHM': 'socialscience',
            'Meta_Astro': 'astrophysics',
            'Meta_LS': 'biomedical',
            'Meta_Journal': 'journal',
            'Meta_CWF': 'computationalworkflow',
        }
        metadata_blocks = dataset_meta.get('data', {}).get('latestVersion', {}).get('metadataBlocks', {})
        return {key: value in metadata_blocks for key, value in metadata_block_map.items()}

    @staticmethod
    def _parse_permission_values(dataset_meta: dict) -> dict:
        permission_info = dataset_meta.get('permission_info', {})
        if permission_info.get('status') == 'NA':
            return {
                'DS_Permission': False,
                'DS_Collab': 'NA',
                'DS_Admin': 'NA',
                'DS_Contrib': 'NA',
                'DS_ContribPlus': 'NA',
                'DS_Curator': 'NA',
                'DS_FileDown': 'NA',
                'DS_Member': 'NA',
            }
        data = permission_info.get('data') or []
        return {
            'DS_Permission': True,
            'DS_Collab': len(data),
            'DS_Admin': len([p for p in data if p.get('_roleAlias') == 'admin']),
            'DS_Contrib': len([p for p in data if p.get('_roleAlias') == 'contributor']),
            'DS_ContribPlus': len([p for p in data if p.get('_roleAlias') == 'fullContributor']),
            'DS_Curator': len([p for p in data if p.get('_roleAlias') == 'curator']),
            'DS_FileDown': len([p for p in data if p.get('_roleAlias') == 'fileDownloader']),
            'DS_Member': len([p for p in data if p.get('_roleAlias') == 'member']),
        }

    def _get_spreadsheet_order(self) -> list[str]:
        with Path(self.spreadsheet_order_file_path).open(encoding='utf-8') as file:
            return file.read().splitlines()

    def _reorder_df_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        order_list = self._get_spreadsheet_order()
        valid_columns = [col for col in order_list if col in df.columns]
        remaining_columns = [col for col in df.columns if col not in valid_columns]
        return df[valid_columns + remaining_columns]

    def make_csv_file(self, meta_dict: dict) -> tuple[Path, str]:
        """Create a CSV file from the nested metadata list.

        Args:
            meta_dict (dict): Dataset metadata dictionary

        Returns:
            tuple[Path, str]: Path to the CSV file, Checksum of the CSV file
        """
        csv_file_path = Path(self.csv_file_dir).joinpath(f'ds_metadata_{get_file_timestamp()}.csv')

        rows = []
        for _, dataset_meta in meta_dict.items():
            raw_data = dataset_meta.get('data', {})
            latest_version_data = raw_data.get('latestVersion', {})

            dataset = DatasetData.model_validate(
                {
                    'id': raw_data.get('id'),
                    'datasetId': latest_version_data.get('datasetId'),
                    'latestVersion': latest_version_data,
                }
            )

            if dataset.latestVersion is None or dataset.latestVersion.metadataBlocks.citation is None:
                continue

            citation = CitationAccessor(dataset.latestVersion.metadataBlocks.citation)

            file_stats = self._get_datafile_meta_usage(dataset_meta)
            file_size = self._get_data_files_size(dataset_meta)
            subject_list: list = citation.get('subject', []) or []
            path_info = dataset_meta.get('dataset_path', 'Unknown')

            row: DatasetExportRow = {
                'DatasetTitle': citation.get('title', '') or '',
                'DatasetURL': (
                    urljoin(
                        self.config.base_url,
                        f'/dataset.xhtml?persistentId={dataset.latestVersion.datasetPersistentId}',
                    )
                    if dataset.latestVersion.datasetPersistentId
                    else ''
                ),
                'DS_Path': path_info,
                'ID': dataset.id,
                'DatasetPersistentId': dataset.latestVersion.datasetPersistentId,
                'DatasetId': dataset.datasetId,
                'VersionState': dataset.latestVersion.versionState,
                'LastUpdateTime': dataset.latestVersion.lastUpdateTime,
                'ReleaseTime': dataset.latestVersion.releaseTime,
                'CreateTime': dataset.latestVersion.createTime,
                'Version': self._get_dataset_version(dataset_meta),
                'FileCount': self._get_data_files_count(dataset_meta),
                'FileSize': file_size,
                'FileSize_normalized': convert_size(file_size),
                'License': (latest_version_data.get('license') or {}).get('name', ''),
                'RestrictedFiles': self._get_restricted_data_files_count(dataset_meta),
                'TermsOfUse': latest_version_data.get('termsOfUse', ''),
                'RequestAccess': latest_version_data.get('fileAccessRequest', False),
                'TermsAccess': latest_version_data.get('termsOfAccess', ''),
                'DF_Hierarchy': file_stats['DF_Hierarchy'],
                'DF_Tags': file_stats['DF_Tags'],
                'DF_Description': file_stats['DF_Description'],
                # Citation — simple/primitive fields
                'CM_Subtitle': citation.get('subtitle', '') or '',
                'CM_AltTitle': citation.get('alternativeTitle', []) or [],
                'CM_AltURL': citation.get('alternativeURL', '') or '',
                'CM_Notes': citation.get('notesText', '') or '',
                'CM_Lang': citation.get('language', []) or [],
                'CM_ProdDate': citation.get('productionDate', '') or '',
                'CM_ProdLocation': citation.get('productionPlace', []) or [],
                'CM_DisDate': citation.get('distributionDate', '') or '',
                'CM_Depositor': citation.get('depositor', '') or '',
                'CM_DepositDate': citation.get('dateOfDeposit', '') or '',
                'CM_DataType': citation.get('kindOfData', []) or [],
                'CM_RelMaterial': citation.get('relatedMaterial', []) or [],
                'CM_RelDatasets': citation.get('relatedDatasets', []) or [],
                'CM_OtherRef': citation.get('otherReferences', []) or [],
                'CM_DataSources': citation.get('dataSources', []) or [],
                'CM_OriginSources': citation.get('originOfSources', '') or '',
                'CM_CharSources': citation.get('characteristicOfSources', '') or '',
                'CM_DocSources': citation.get('accessToSources', '') or '',
                # Citation — compound fields (extract specific child values)
                'CM_Agency': citation.get_compound_values('otherId', 'otherIdAgency'),
                'CM_ID': citation.get_compound_values('otherId', 'otherIdValue'),
                'CM_Author': citation.get_compound_values('author', 'authorName'),
                'CM_NumberAuthors': len(citation.get_compound_values('author', 'authorName')),
                'CM_AuthorAff': citation.get_compound_values('author', 'authorAffiliation'),
                'CM_AuthorIDType': citation.get_compound_values('author', 'authorIdentifierScheme'),
                'CM_AuthorID': citation.get_compound_values('author', 'authorIdentifier'),
                'CM_ContactName': citation.get_compound_values('datasetContact', 'datasetContactName'),
                'CM_ContactAff': citation.get_compound_values('datasetContact', 'datasetContactAffiliation'),
                'CM_Descr': citation.get_compound_values('dsDescription', 'dsDescriptionValue'),
                'CM_DescrDate': citation.get_compound_values('dsDescription', 'dsDescriptionDate'),
                'CM_Subject': subject_list,
                **self._get_dataset_subjects(subject_list),
                'CM_Keyword': citation.get_compound_values('keyword', 'keywordValue'),
                'CM_KeywordVocab': citation.get_compound_values('keyword', 'keywordVocabulary'),
                'CM_KeywordURI': citation.get_compound_values('keyword', 'keywordVocabularyURI'),
                'CM_TopicTerm': citation.get_compound_values('topicClassification', 'topicClassValue'),
                'CM_TopicVocab': citation.get_compound_values('topicClassification', 'topicClassVocab'),
                'CM_TopicURL': citation.get_compound_values('topicClassification', 'topicClassVocabURI'),
                'CM_PubCit': citation.get_compound_values('publication', 'publicationCitation'),
                'CM_PubIDType': citation.get_compound_values('publication', 'publicationIDType'),
                'CM_PubID': citation.get_compound_values('publication', 'publicationIDNumber'),
                'CM_PubURL': citation.get_compound_values('publication', 'publicationURL'),
                'CM_ProdName': citation.get_compound_values('producer', 'producerName'),
                'CM_ProdAff': citation.get_compound_values('producer', 'producerAffiliation'),
                'CM_ProdAbbrev': citation.get_compound_values('producer', 'producerAbbreviation'),
                'CM_ProdURL': citation.get_compound_values('producer', 'producerURL'),
                'CM_ProdLogo': citation.get_compound_values('producer', 'producerLogoURL'),
                'CM_ContribName': citation.get_compound_values('contributor', 'contributorName'),
                'CM_ContribType': citation.get_compound_values('contributor', 'contributorType'),
                'CM_FundingAgency': citation.get_compound_values('grantNumber', 'grantNumberAgency'),
                'CM_FundingID': citation.get_compound_values('grantNumber', 'grantNumberValue'),
                'CM_DisName': citation.get_compound_values('distributor', 'distributorName'),
                'CM_DisAff': citation.get_compound_values('distributor', 'distributorAffiliation'),
                'CM_DisAbbrev': citation.get_compound_values('distributor', 'distributorAbbreviation'),
                'CM_DisURL': citation.get_compound_values('distributor', 'distributorURL'),
                'CM_DisLogoURL': citation.get_compound_values('distributor', 'distributorLogoURL'),
                'CM_TimeStart': citation.get_compound_values('timePeriodCovered', 'timePeriodCoveredStart'),
                'CM_TimeEnd': citation.get_compound_values('timePeriodCovered', 'timePeriodCoveredEnd'),
                'CM_CollectionStart': citation.get_compound_values('dateOfCollection', 'dateOfCollectionStart'),
                'CM_CollectionEnd': citation.get_compound_values('dateOfCollection', 'dateOfCollectionEnd'),
                'CM_SeriesName': citation.get_compound_values('series', 'seriesName'),
                'CM_SeriesInfo': citation.get_compound_values('series', 'seriesInformation'),
                'CM_SoftwareName': citation.get_compound_values('software', 'softwareName'),
                'CM_SoftwareVers': citation.get_compound_values('software', 'softwareVersion'),
                # Metadata blocks presence
                **self._get_metadata_blocks_usage(dataset_meta),
                # Permission role counts
                **self._parse_permission_values(dataset_meta),
            }

            rows.append(self.serialize_row(row))

        df = pd.DataFrame(rows)
        df = self._reorder_df_columns(df)

        df.to_csv(csv_file_path, index=False)

        checksum = gen_checksum(csv_file_path)
        logger.info(f'Exported Dataset Metadata CSV: {csv_file_path}\nChecksum (SHA-256): {checksum}')

        return csv_file_path, checksum
