"""Models for the API responses."""

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ruff: noqa: N815


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


class DatasetField(BaseModel):
    """Base Dataverse metadata field."""

    typeName: str
    typeClass: Literal[
        'primitive',
        'compound',
        'controlledVocabulary',
    ]
    multiple: bool = False
    value: object


class MetadataBlock(BaseModel):
    """Dataverse metadata block."""

    displayName: str | None = None
    name: str
    fields: list[DatasetField]

    @property
    def field_map(self) -> dict[str, DatasetField]:
        """Return fields indexed by typeName."""
        return {field.typeName: field for field in self.fields}

    def get_field(
        self,
        field_name: str,
    ) -> DatasetField | None:
        """Return a DatasetField by typeName."""
        return self.field_map.get(field_name)

    def get_value(
        self,
        field_name: str,
        default: object = None,
    ) -> object:
        """Return field value."""
        field = self.get_field(field_name)

        if field is None:
            return default

        return field.value


class MetadataBlocks(BaseModel):
    """Dataverse metadata blocks."""

    citation: MetadataBlock | None = None


class LatestVersion(BaseModel):
    """Dataverse latest version."""

    datasetPersistentId: str | None = None
    versionState: str | None = None
    lastUpdateTime: str | None = None
    releaseTime: str | None = None
    createTime: str | None = None

    metadataBlocks: MetadataBlocks


class DatasetData(BaseModel):
    """Dataverse dataset."""

    id: int | None = None
    datasetId: int | None = None

    latestVersion: LatestVersion | None = None


class CitationAccessor:
    """Helper for citation metadata."""

    def __init__(
        self,
        citation_block: MetadataBlock,
    ) -> None:
        self.block = citation_block

    def get(
        self,
        field_name: str,
        default: object = None,
    ) -> object:
        """Return raw field value."""
        return self.block.get_value(
            field_name,
            default,
        )

    def get_compound_values(
        self,
        field_name: str,
        child_field: str,
    ) -> list[object]:
        """Return values from compound fields."""
        rows = self.get(field_name, [])

        result = []

        for row in rows:
            child = row.get(child_field)

            if child:
                result.append(
                    child.get('value'),
                )

        return result
