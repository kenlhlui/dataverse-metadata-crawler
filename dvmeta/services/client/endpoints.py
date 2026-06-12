"""The dataverse API endpoints used in the crawler."""


class Endpoints:
    """Endpoints for the Dataverse API."""

    @staticmethod
    def search() -> str:
        """The search endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/search.html

        Returns:
            str: The search endpoint
        """
        return 'api/search'

    @staticmethod
    def ds_json(dataset_id: str | int, draft: bool = False) -> str:
        """The dataset JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-json-representation-of-a-dataset

        Args:
            dataset_id (str | int): The database ID of the dataset
            draft (bool): Whether to fetch the draft version

        Returns:
            str: The dataset JSON representation endpoint
        """
        url = f'api/datasets/{dataset_id}'

        if draft:
            url += '/:draft'
        return url

    @staticmethod
    def ds_permissions(dataset_id: str | int) -> str:
        """The dataset permissions endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#list-role-assignments-in-a-dataset

        Args:
            dataset_id (str | int): The database ID of the dataset

        Returns:
            str: The dataset permissions endpoint
        """
        return f'api/datasets/{dataset_id}/assignments'

    @staticmethod
    def ds_meta_exporters(persistent_id: str, exporter: str = 'dataverse_json', version: str | None = None) -> str:
        """The dataset metadata exporters endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#export-metadata-of-a-dataset-in-various-formats

        Note: This is mainly for getting the path of the dataset from OAI_ORE metadata. It works the best with No version provided.

        Args:
            persistent_id (str): The persistent ID of the dataset
            version (str | None): The version of the dataset
            exporter (str): The metadata exporter format (e.g., 'dataverse_json', 'OAI_ORE')

        Returns:
            str: The dataset metadata exporters endpoint
        """  # noqa: E501, W505
        if version is not None and isinstance(version, str):
            return f'api/datasets/export?exporter={exporter}&persistentId={persistent_id}&version={version}'
        return f'api/datasets/export?exporter={exporter}&persistentId={persistent_id}'

    @staticmethod
    def dv_json(dataverse_id: str) -> str:
        """The dataverse JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#view-a-dataverse-collection

        Args:
            dataverse_id (str): The database ID or alias of a dataverse collection. Can also be speical value `root` for the root collection.

        Returns:
            str: The dataverse JSON representation endpoint

        """
        return f'api/dataverses/{dataverse_id}'

    @staticmethod
    def user_info() -> str:
        """The user info endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-user-information-in-json-format

        Returns:
            str: The user info endpoint
        """
        return 'api/users/:me'

    @staticmethod
    def version_info() -> str:
        """The version info endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#show-dataverse-software-version-and-build-number

        Returns:
            str: The version info endpoint
        """
        return 'api/info/version'
