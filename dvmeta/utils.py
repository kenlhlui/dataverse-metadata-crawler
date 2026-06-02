"""This module contains utility functions for the dvmeta package."""

import math
import os
from hashlib import sha256
from pathlib import Path

import orjson
from dotenv import load_dotenv
from loguru import logger

from dvmeta.dirmanager import DirManager
from dvmeta.models import Config
from dvmeta.timestamp import get_file_timestamp


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
    json_dir = DirManager().json_files_dir()
    json_file_path = Path(json_dir, f'{file_name}_{get_file_timestamp()}.json')
    if data_dict:
        with json_file_path.open('wb') as file:  # Open file in binary write mode
            file.write(orjson.dumps(data_dict, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
        checksum = gen_checksum(json_file_path)
        logger.info(f'Exported {file_name} to json file: {json_file_path}\nChecksum (SHA-256): {checksum}')

        return json_file_path, checksum
    logger.info(f'{file_name} is empty, no json file is created.')

    return None, None


def load_env() -> Config:
    """Load the environment variables.

    Returns:
        Config: A Config instance populated from environment variables
    """
    load_dotenv()
    api_key = os.getenv('API_KEY') or None
    base_url = os.getenv('BASE_URL', '')

    return Config(api_key=api_key, base_url=base_url)
