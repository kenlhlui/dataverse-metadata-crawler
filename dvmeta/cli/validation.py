"""This module contains functions for validating command line arguments and environment variables."""

from click import MissingParameter
from loguru import logger
from pydantic import ValidationError
from typer import BadParameter

from dvmeta.http import HttpxClient
from dvmeta.models import Config
from dvmeta.models import DatasetVersion


def validate_spreadsheet_option(value: bool, dvdfds_metadata: bool) -> bool:
    """Validate the value of --spreadsheet argument.

    Args:
        value (bool): Value of --spreadsheet argument.
        dvdfds_metadata (bool): Value of --dvdfds_metadata argument.

    Returns:
        bool: Value of --spreadsheet argument if it is valid.
    """
    if value and not dvdfds_metadata:
        msg = 'The --spreadsheet option can only be used if --dvdfds_metadata is set to True.'
        raise BadParameter(msg)
    return value


def validate_version_type(value: str) -> str | float:
    """Validate the value of --version argument.

    Args:
        value (str): Value of --version argument.

    Returns:
        str | float: Value of --version argument if it is valid.

    Raises:
        BadParameter: If the value is not valid.
    """
    value = value.lower().strip()

    try:
        model = DatasetVersion.model_validate({'version': value})
        return model.version
    except ValidationError:
        msg = 'Must be "draft", "latest", "latest-published", or a number like "1" or "1.2".'
        msg = f'Invalid version: {value}. Must be "draft", "latest", "latest-published", or a number like "1" or "1.2".'
        raise BadParameter(msg)


def validate_basic_input(dvdfds_matadata_option: bool, permission_option: bool) -> None:
    """Validate the basic input options.

    Args:
        dvdfds_matadata_option (bool): Value of --dvdfds_metadata argument.
        permission_option (bool): Value of --permission argument.

    Raises:
        MissingParameter: If the combination of options is invalid.
    """
    if not dvdfds_matadata_option and not permission_option:
        msg = 'Please provide the type of metadata to crawl. Use -d or/and -p flag for crawling of dataset metadata or permission metadata, respectively.'  # noqa: E501
        raise MissingParameter(msg, param_type='parameter')


def validate_api_token_presence(permission_option: bool, config: Config) -> None:
    """Validate whether API_KEY is supplied when crawling permission metadata option is enabled.

    Args:
        permission_option (bool): Value of -p argument.
        config (Config): The config

    Raises:
        MissingParameter: If the combination of options is invalid.
    """
    if permission_option and (config.api_key is None or config.api_key == 'None'):
        msg = 'Crawling permission metadata requires API Token. Please provide the API Token. Exiting...'
        raise MissingParameter(msg, param_type='parameter')


def validate_connection(config: Config) -> bool:
    """Validate connection to the Dataverse repository.

    Args:
        config (Config): The config.

    Returns:
        bool: True if the API key is valid, False otherwise.

    Raises:
        BadParameter: If connection to the repository fails.
    """
    logger.info('Checking the connection to the Dataverse repository...')
    client = HttpxClient(config)

    if config.api_key:
        result = client.authenticate_api_key()
        if result is True:
            msg = f'Connection to the dataverse repository {config.base_url} with API Token is successful.'
            logger.info(msg)
            return True
        if result is False:
            msg = 'Failed to authenticate the API Token with the repository. Will try to crawl without the API Token.'
            logger.warning(msg)

    # Always check basic connection whether API auth failed or wasn't provided
    client = HttpxClient(config)
    result = client.authenticate_dv_connection()
    if result is False:
        msg = f'Failed to connect to the dataverse repository: {config.base_url}. Exiting...'
        logger.error(msg)
        raise BadParameter(msg)

    logger.info(f'Connection to the dataverse repository {config.base_url} is successful.')
    return False
