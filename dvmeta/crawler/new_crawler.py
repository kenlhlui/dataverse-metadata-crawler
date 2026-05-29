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
        self.config = self._define_headers(config)
        self.endpoints = Endpoints(config.base_url)
        self.client = HttpxClient(self.config)

    @staticmethod
    def _define_headers(config: Config) -> Config:
        """Define the headers for the HTTP request.

        Args:
            config (Config): Configuration

        Returns:
            Config: Config with updated headers
        """
        headers = {'Accept': 'application/json'}

        if config.api_key and str(config.api_key).lower() != 'none':
            headers['X-Dataverse-key'] = config.api_key

        config.headers = headers

        return config

    def get_all_dataverse_datasets(self, metadata_source: str | None = None) -> list:
        """Get all datasets in the Dataverse collection (recursively, including all the children).

        Uses the Search API.

        Args:
            metadata_source (str | None): Optional filter for metadata source (e.g., 'Borealis', 'Dataverse'). This is to exclude the harvested datasets. (docs: https://github.com/IQSS/dataverse/issues/9515). If no value is provided, it will fetch all datasets regardless of the metadata source.

        Returns:
            list: A list of dataset metadata dictionaries
        """  # noqa: W505, E501
        search_url = self.endpoints.search()
        params = {
            'q': '*',
            'per_page': 1000,  # Adjust as needed # TODO: make this adjustable via config or CLI option
            'type': 'dataset',
            'start': 0,  # Pagination start index
            'subtree': self.config.collection_alias,  # Search within the specified collection # TODO: make this more flexible to allow multiple collections (e.g. &subtree=birds&subtree=cats)  # noqa: E501
            'show_collections': True,
            'query_entities': False,  # Make the query faster by not fetching the entities
            'show_entity_ids': True,
        }

        if metadata_source:
            params['fq'] = f'metadata_source:{metadata_source}'

        datasets = []

        while True:
            logger.debug(f'Fetching datasets with start={params["start"]} from Search API...')
            response = self.client.sync_get(search_url, params=params)
            logger.debug(
                f'Search API response for start={params["start"]}: {response.text if response else "No response"}'
            )
            if response is None:
                break

            data = response.json()
            items = data.get('data', {}).get('items', [])
            if not items:
                break

            for item in items:
                datasets.append(item)

            params['start'] += params['per_page']

        return datasets

    async def get_dataset_metadata(self, dataset_ids: list, draft: bool = False) -> list:
        """Get the metadata of a dataset using the dataset Native API endpoint.

        Args:
            dataset_ids (list): A list of dataset (entity) IDs
            draft (bool): Whether to fetch the draft version

        Returns:
            list: A list of dataset metadata dictionaries
        """
        url_list = [self.endpoints.ds_json(dataset_id, draft=draft) for dataset_id in dataset_ids]

        response = await self.client.async_get(url_list)

        return [res.json() for res in response if res is not None]
