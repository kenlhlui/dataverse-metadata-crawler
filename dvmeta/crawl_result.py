"""Data model for the crawl result."""

from dataclasses import dataclass


@dataclass
class CrawlResult:
    """Collected data returned from the crawling pipeline."""

    meta_dict: dict
    export_data: list
    failed_metadata_uris: dict
    pid_dict_dd: dict
    collections_tree_flatten: dict
