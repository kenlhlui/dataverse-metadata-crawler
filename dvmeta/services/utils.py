"""This module contains utility functions for the dvmeta package."""

import math
from hashlib import sha256
from pathlib import Path

import jmespath
import orjson
from loguru import logger

from dvmeta.services.dir_manager import DirManager
from dvmeta.services.dir_manager import ExportDir
from dvmeta.services.timestamp import get_file_timestamp


def count_key(key: dict | list | tuple) -> int:
    """Count the number of keys in a dictionary, list or tuple.

    Args:
        key (dict, list, tuple): The dictionary, list or tuple to count the keys of.

    Returns:
        int: The number of keys in the dictionary, list or tuple.
    """
    return len(key) if isinstance(key, (dict, list, tuple)) else 0


def convert_size(size_bytes: int | str) -> str:
    """Convert the size of a file from bytes to a human-readable format.

    Args:
        size_bytes (int): The size of the file in bytes.

    Returns:
        str: The size of the file in a human-readable format
    """
    if not isinstance(size_bytes, int):
        return 'Error'
    if size_bytes == 0:
        return '0B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f'{s} {size_name[i]}'


def gen_checksum(file_path: Path) -> str:
    """Generate a SHA-256 checksum for a file.

    Args:
        file_path (Path): The path to the file for which to generate the checksum.

    Returns:
        str: The SHA-256 checksum of the file.
    """
    sha256_hash = sha256()
    with file_path.open('rb') as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()  # Return the hexadecimal digest of the hash


def list_to_string(list: list) -> str:
    """Joins list items into comma-separated string after converting to string and stripping whitespace.

    Args:
        list (list): A list of values to be processed.

    Returns:
        str: A single string with the processed values separated by commas.
    """
    # Ensure each value is a string and strip whitespace from each string
    stripped_values = [str(value).strip() for value in list]

    # Join the stripped strings with a comma
    return ', '.join(stripped_values)


def orjson_export(data_dict: dict, file_name: str) -> tuple:
    """Export a dictionary to a json file using the orjson library.

    Args:
        data_dict (dict): The dictionary to export to a json file.
        file_name (str): The name of the json file to create.

    Returns:
        tuple(Path, str): A tuple containing the path to the created json file and its checksum.
    """
    json_dir = DirManager().get_dir(ExportDir.JSON)
    json_file_path = Path(json_dir, f'{file_name}_{get_file_timestamp()}.json')
    if data_dict:
        with json_file_path.open('wb') as file:  # Open file in binary write mode
            file.write(orjson.dumps(data_dict, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
        checksum = gen_checksum(json_file_path)
        logger.info(f'Exported {file_name} to json file: {json_file_path}\nChecksum (SHA-256): {checksum}')

        return json_file_path, checksum
    logger.info(f'{file_name} is empty, no json file is created.')

    return None, None


def get_data_files_size(dictionary: dict) -> int | str:
    """Calculate the total size of data files in bytes from a dataset metadata dictionary.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via 'data.latestVersion.files'.

    Returns:
        int: The total size of data files in bytes if the structure is correct and files are present.

        str: 'Error' if the input is not a dictionary or if the expected structure is not found.
    """  # noqa: E501, W505
    latest_version = dictionary.get('data', {}).get('latestVersion', {})
    if latest_version.get('files'):
        data_files_size_list: list = jmespath.search('data.latestVersion.files[*].dataFile.filesize|[]', dictionary)
        if data_files_size_list:
            return sum(data_files_size_list)
    else:
        return 0
    return 'Error'


def get_collection_files_size(dictionary: dict) -> int | str:
    """Calculate the total size of collection files in bytes from a dataset metadata dictionary.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via '{dataset_id}.data.latestVersion.files'.
    """  # noqa: E501, W505
    total_size = 0

    for _, dataset in dictionary.items():
        ds_size = get_data_files_size(dataset)
        total_size += ds_size if isinstance(ds_size, int) else 0
    return total_size


def get_data_files_count(dictionary: dict) -> int | str:
    """Calculate the total number of data files from a dataset metadata dictionary.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via 'data.latestVersion.files'.

    Returns:
        int | str: The total number of data files if the structure is correct and files are present, otherwise 'Error'.
    """  # noqa: E501, W505
    latest_version = dictionary.get('data', {}).get('latestVersion', {})
    if 'files' in latest_version:
        return len(latest_version['files'])
    return 'Error'


def get_collection_files_count(dictionary: dict) -> int | str:
    """Calculate the total number of data files from a dataset metadata dictionary of a collection.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via '{dataset_id}.data.latestVersion.files'.
    """  # noqa: E501, W505
    total_count = 0

    for _, dataset in dictionary.items():
        ds_count = get_data_files_count(dataset)
        total_count += ds_count if isinstance(ds_count, int) else 0
    return total_count
