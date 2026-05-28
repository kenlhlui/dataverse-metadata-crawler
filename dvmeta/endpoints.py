"""The dataverse API endpoints used in the crawler."""

from urllib.parse import urljoin


class Endpoints:
    """Endpoints for the Dataverse API."""

    def __init__(self, base_url: str) -> None:
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
        if draft:
            return urljoin(self.base_url, f'/api/datasets/{dataset_id}/:draft')
        return urljoin(self.base_url, f'/api/datasets/{dataset_id}')
