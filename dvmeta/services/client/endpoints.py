"""The dataverse API endpoints used in the crawler."""

from urllib.parse import urljoin


class Endpoints:
    """Endpoints for the Dataverse API."""

    def __init__(self, base_url: str) -> None:
        """Initialize the Endpoints class with the base URL of the Dataverse instance."""
        self.base_url = base_url

    def search(self) -> str:
        """The search endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/search.html

        Returns:
            str: The search endpoint URL
        """
        return urljoin(self.base_url, '/api/search')

    def ds_json(self, dataset_id: str | int, draft: bool = False) -> str:
        """The dataset JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-json-representation-of-a-dataset

        Args:
            dataset_id (str | int): The database ID of the dataset
            draft (bool): Whether to fetch the draft version

        Returns:
            str: The dataset JSON representation endpoint URL
        """
        url = urljoin(self.base_url, f'/api/datasets/{dataset_id}')

        if draft:
            url += '/:draft'
        return url

    def ds_permissions(self, dataset_id: str | int) -> str:
        """The dataset permissions endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#list-role-assignments-in-a-dataset

        Args:
            dataset_id (str | int): The database ID of the dataset

        Returns:
            str: The dataset permissions endpoint URL
        """
        return urljoin(self.base_url, f'/api/datasets/{dataset_id}/assignments')

    def ds_meta_exporters(self, persistent_id: str, version: str, exporter: str = 'dataverse_json') -> str:
        """The dataset metadata exporters endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#export-metadata-of-a-dataset-in-various-formats

        Args:
            persistent_id (str): The persistent ID of the dataset
            version (str): The version of the dataset
            exporter (str): The metadata exporter format (e.g., 'dataverse_json', 'OAI_ORE')

        Returns:
            str: The dataset metadata exporters endpoint URL
        """
        endpoint = f'/api/datasets/export?exporter={exporter}&persistentId={persistent_id}&version=:{version}'
        return urljoin(self.base_url, endpoint)

    def dv_json(self, dataverse_id: str) -> str:
        """The dataverse JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#view-a-dataverse-collection

        Args:
            dataverse_id (str): The database ID or alias of a dataverse collection. Can also be speical value `root` for the root collection.

        Returns:
            dict: The dataverse JSON representation endpoint

        """
        return urljoin(self.base_url, f'/api/dataverses/{dataverse_id}')
