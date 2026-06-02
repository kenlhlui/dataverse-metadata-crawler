"""The new crawler module for dvmeta.

Flow:
1. Use the search API -> Get all the datasets in the Dataverse collection (including all the children)
2. For each dataset, get the metadata using the dataset Native API endpoint
3. Have the option to get the path using the OAIMPH endpoint
4. Have the option to get the permission metadata for each dataset
5. Export the metadata to JSON and CSV files


"""

from loguru import logger

from dvmeta.endpoints import Endpoints
from dvmeta.http import HttpxClient
from dvmeta.models import Config


class MetaDataCrawler:
    """Crawl metadata of datasets in a collection."""

    def __init__(self, config: Config) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config
        self.endpoints = Endpoints(config.base_url)
        self.client = HttpxClient(self.config)

    def get_dataverse_ds_records(
        self, metadata_source: str | None = None, publication_status: str | None = None
    ) -> list:
        """Get the dataset records in the Dataverse collection (recursively, including all the children).

        Uses the Search API.

        Args:
            metadata_source (str | None): Optional filter for metadata source (e.g., 'Borealis', 'Dataverse'). This is to exclude the harvested datasets. (docs: https://github.com/IQSS/dataverse/issues/9515). If no value is provided, it will fetch all datasets regardless of the metadata source.
            publication_status (str | None): Optional filter for publication status (e.g., 'Published', 'Draft', 'Unpublished', 'Deaccessioned'). If no value is provided, it will fetch all datasets regardless of the publication status. See the 'facets' section in the Search API return for the possible values.

        Returns:
            list: A list of dataset metadata dictionaries
        """  # noqa: W505, E501
        search_url = self.endpoints.search()
        per_page = 1000
        start = 0

        ds_records = []

        while True:
            params = [
                ('q', '*'),
                ('per_page', per_page),
                ('type', 'dataset'),
                ('start', start),
                ('subtree', self.config.collection_alias),
                ('show_collections', True),
                ('query_entities', False),
                ('show_entity_ids', True),
            ]

            if metadata_source:
                params.append(('fq', f'metadataSource:"{metadata_source}"'))

            if publication_status:
                params.append(('fq', f'publicationStatus:"{publication_status}"'))

            logger.debug(f'Fetching datasets with params {params} from Search API...')
            response = self.client.sync_get(search_url, params=params)

            if response is None:
                break

            data = response.json()
            items = data.get('data', {}).get('items', [])
            if not items:
                break

            ds_records.extend(items)
            start += per_page

        return ds_records

    async def get_dataset_metadata(self, dataset_ids: list, draft: bool = False) -> dict:
        """Get the metadata of a dataset using the dataset Native API endpoint.

        Args:
            dataset_ids (list): A list of dataset (entity) IDs
            draft (bool): Whether to fetch the draft version

        Returns:
            dict: A dictionary mapping dataset IDs to their metadata
        """
        url_list = [self.endpoints.ds_json(dataset_id, draft=draft) for dataset_id in dataset_ids]

        response = await self.client.async_get(url_list)

        return {
            dataset_id: res.json() for dataset_id, res in zip(dataset_ids, response, strict=False) if res is not None
        }

    async def get_oaiore_metadata(self, pids: list, version: str = 'latest') -> dict:
        """Get the metadata of datasets in OAI_ORE format.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#export-metadata-of-a-dataset-in-various-formats

        Note: This is mainly for getting the path of the dataset, which is not available in the dataset JSON (dataverse_json) metadata.

        Args:
            pids (list): A list of dataset (entity) IDs
            version (str): The version of the dataset
        """  # noqa: W505, E501
        url_list = [
            self.endpoints.ds_meta_exporters(persistent_id=str(pid), version=version, exporter='OAI_ORE')
            for pid in pids
        ]

        response = await self.client.async_get(url_list)

        return {pid: res.json() for pid, res in zip(pids, response, strict=False) if res is not None}

    async def get_dataset_permissions(self, dataset_ids: list) -> dict:
        """Get the permission metadata of a dataset using the dataset permissions API endpoint.

        Args:
            dataset_ids (list): A list of dataset (entity) IDs

        Returns:
            dict: A dictionary mapping dataset IDs to their permission metadata
        """
        url_list = [self.endpoints.ds_permissions(dataset_id) for dataset_id in dataset_ids]

        response = await self.client.async_get(url_list)

        return {
            dataset_id: res.json() for dataset_id, res in zip(dataset_ids, response, strict=False) if res is not None
        }
