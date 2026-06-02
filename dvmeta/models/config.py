"""Module for the configuration settings of the metadata crawler."""

from pydantic import BaseModel
from pydantic import ConfigDict


class Config(BaseModel):
    """Model for the configuration settings."""

    model_config = ConfigDict(frozen=False)

    api_key: str | None = None
    base_url: str
    version: str = ''
    collection_alias: str = ''
    collection_id: int | str | None = None
    collection_name: str | None = None
    metadata_source: str | None = None
    semaphore: int = (
        5  # Default number of concurrent requests for async operations, can be overridden by method parameters
    )
