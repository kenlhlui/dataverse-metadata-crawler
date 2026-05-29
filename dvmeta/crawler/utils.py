"""utility functions for crawler."""

from typing import Literal

from loguru import logger


def parse_search_response(
    search_response: list[dict], publication_status: Literal['Draft', 'Published', 'Unpublished'] | None = None
) -> list:
    """Parse the search response to extract dataset metadata.

    Args:
        search_response (list[dict]): The response from the search API.
        publication_status (Literal['Draft', 'Published', 'Unpublished'] | None): The publication status to filter by.

    Returns:
        list: A list of dataset metadata dictionaries.
    """
    items: list[dict] = search_response.get('data', {}).get('items', [])

    if publication_status:
        items = [item for item in items if publication_status in item.get('publicationStatuses', [])]

    if not items:
        logger.warning('No items found in the search response.')
        return []
    return [item.get('entity_id') for item in items]
