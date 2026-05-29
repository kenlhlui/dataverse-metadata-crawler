"""Models for the API responses."""

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class CollectionData(BaseModel):
    """Model for collection data."""

    id: str | int  # Accept both string and integer for id
    alias: str
    name: str


class DvResponse(BaseModel):
    """Model for the collections tree response."""

    status: str
    data: dict


class CollectionsTreeResponseData(BaseModel):
    """Model for the collections tree response data."""

    status: str
    data: CollectionData | None = Field(default=None, description='The collections tree data')


class DatasetVersion(BaseModel):
    """Permitted dataset version type."""

    version: Literal['draft', 'latest', 'latest-published'] | float | int


class Config(BaseModel):
    """Model for the configuration settings."""

    model_config = ConfigDict(frozen=False)

    api_key: str | None = None
    base_url: str
    version: str = ''
    collection_alias: str = ''
    collection_id: int | str | None = None
    collection_name: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    metadata_source: str | None = None
