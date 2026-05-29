"""utility functions for crawler."""

from typing import Literal

from loguru import logger


def parse_search_response(
    items: list[dict], publication_status: Literal['Draft', 'Published', 'Unpublished'] | None = None
) -> list:
    """Parse the search response to extract dataset metadata.

    Args:
        items (list[dict]): The items field returned by the Search API response, which is a list of dataset metadata dictionaries.
        publication_status (Literal['Draft', 'Published', 'Unpublished'] | None): The publication status to filter by.

    Returns:
        list: A list of dataset metadata dictionaries.
    """  # noqa: E501, W505
    if publication_status:
        items = [item for item in items if publication_status in item.get('publicationStatuses', [])]

    if not items:
        logger.warning('No items found in the search response.')
        return []
    return [item.get('entity_id') for item in items]


def extract_path(node: dict, dataset_name: str) -> str:
    """Walk schema:isPartOf chain from leaf to root, return ordered path."""
    path = []
    current = node
    while current:
        path.append(
            {
                'name': current.get('schema:name'),
                'id': current.get('@id'),
            }
        )
        current = current.get('schema:isPartOf')

    collections_path = '/'.join(p['name'] for p in reversed(path))

    return collections_path + '/' + dataset_name


def get_path_from_oaiore(oaiore_response: dict) -> str | None:
    """Extract the dataset path from the OAI_ORE metadata.

    Args:
        oaiore_response (dict): The OAI_ORE metadata response.
        dataset_name (str): The name of the dataset to find in the OAI_ORE response.

    Returns:
        str | None: The dataset path if found, otherwise None.
    """
    dataset_name = oaiore_response.get('ore:describes', {}).get('schema:name')
    ispartof = oaiore_response.get('ore:describes', {}).get('schema:isPartOf', [])
    if not ispartof:
        logger.debug('No schema:isPartOf found in the OAI_ORE response.')
        return None

    return extract_path(ispartof, dataset_name)
