"""Module for the configuration settings of the metadata crawler."""

from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Config(BaseSettings):
    """Model for the configuration settings."""

    model_config = SettingsConfigDict(env_file='.env')

    api_key: str | None = Field(
        None,
        validation_alias=AliasChoices(
            'API_TOKEN',
            'API_KEY',
        ),
    )
    base_url: str | None = Field(
        'https://borealisdata.ca/',
    )
    version: str = ''
    collection_alias: str = ''
    collection_id: int | str | None = None
    collection_name: str | None = None
    metadata_source: str | None = None
    semaphore_limit: int = (
        5  # Default number of concurrent requests for async operations, can be overridden by method parameters
    )
