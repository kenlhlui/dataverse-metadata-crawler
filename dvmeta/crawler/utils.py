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

    return list(dict.fromkeys([item.get('entity_id') for item in items]))  # remove duplicates while preserving order


def get_pids_from_search_response(items: list[dict]) -> dict:
    """Parse the search response to extract dataset PIDs.

    Args:
        items (list[dict]): The items field returned by the Search API response, which is a list of dataset metadata dictionaries.

    Returns:
        dict: A dictionary mapping dataset (entity) IDs to their PIDs.
    """
    return {item.get('entity_id'): item.get('global_id') for item in items if item.get('global_id') is not None}


def merge_oaiore_to_meta_dict(meta_dict: dict, oaiore_metadata: dict) -> dict:
    """Merge OAI-ORE metadata into the meta_dict.

    Args:
        meta_dict (dict): The original metadata dictionary containing dataset metadata.
        oaiore_metadata (dict): The OAI-ORE metadata dictionary to merge, which contains dataset paths.

    Returns:
        dict: The merged metadata dictionary with OAI-ORE metadata included.
    """
    for dataset_id, dataset_meta in meta_dict.items():
        dataset_pid = dataset_meta.get('data', {}).get('latestVersion', {}).get('datasetPersistentId')
        oaiore_meta = oaiore_metadata.get(dataset_pid)
        if oaiore_meta:
            path = get_path_from_oaiore(oaiore_meta)
            if path:
                dataset_meta['dataset_path'] = path
            else:
                logger.debug(f'No valid path found in OAI-ORE metadata for dataset ID {dataset_id}.')
        else:
            logger.debug(f'No OAI-ORE metadata found for dataset ID {dataset_id}.')

    return meta_dict


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
        return None

    return extract_path(ispartof, dataset_name)


def merge_permission_to_meta_dict(meta_dict: dict, permission_metadata: dict) -> dict:
    """Merge permission metadata into the meta_dict.

    Args:
        meta_dict (dict): The original metadata dictionary containing dataset metadata.
        permission_metadata (dict): The permission metadata dictionary to merge, which contains dataset permissions.

    Returns:
        dict: The merged metadata dictionary with permission metadata included.
    """
    for dataset_id, dataset_meta in meta_dict.items():
        permissions = permission_metadata.get(dataset_id)
        if permissions is not None:
            dataset_meta['permissions'] = permissions
        else:
            logger.debug(f'No permission metadata found for dataset ID {dataset_id}.')

    return meta_dict
