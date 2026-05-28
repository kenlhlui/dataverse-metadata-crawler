"""Async crawling workers for the CLI."""

from dataclasses import dataclass

from loguru import logger

from dvmeta.crawler import MetaDataCrawler
from dvmeta.exporter import ExportManager
from dvmeta.models import Config
from dvmeta.parser import Parsing
from dvmeta.spreadsheet import Spreadsheet
from dvmeta.utils import count_key


@dataclass
class CrawlOptions:
    """Boolean flags controlling which metadata is crawled and exported."""

    dvdfds_matadata: bool
    permission: bool
    empty_dv: bool
    spreadsheet: bool
    failed: bool


async def run_crawl(
    config: Config,
    metadata_crawler: MetaDataCrawler,
    collections_tree: dict,
    options: CrawlOptions,
) -> tuple:
    """Run the main crawling pipeline and return collected data."""
    permission_dict = {}

    parsing = Parsing(config, collections_tree)

    logger.info('Getting basic metadata of datasets in across dataverses (incl. all children)...')
    dataverse_contents, _ = await metadata_crawler.get_dataverse_contents(parsing.collection_id_list)
    parsing.add_path_to_dataverse_contents(dataverse_contents)
    empty_dv_dict, ds_dict = parsing.get_pids()

    meta_dict = {}
    failed_metadata_uris = {}
    pid_dict_dd = {}

    export_manager = ExportManager()

    if options.dvdfds_matadata:
        logger.info('Crawling Representation and File metadata of datasets...')
        pid_list = [item['datasetPersistentId'] for item in ds_dict.values()]
        meta_dict, failed_metadata_uris = await metadata_crawler.get_datasets_meta(pid_list)

        parsing.replace_key_with_dataset_id(meta_dict)  # TEMPORARY FIX
        meta_dict, pid_dict_dd = parsing.add_path_info(ds_dict)
        failed_metadata_uris = parsing.rm_dd_from_failed_uris(failed_metadata_uris, pid_dict_dd)

        export_manager.export(pid_dict_dd, 'pid_dict_dd')

        if options.failed:
            export_manager.export(failed_metadata_uris, 'failed_metadata_uris')

    if options.permission:
        logger.info('Crawling Permission metadata of datasets...')
        ds_id_list = [item['datasetId'] for item in ds_dict.values()]
        permission_dict, _ = await metadata_crawler.get_datasets_permissions(ds_id_list)

        if not options.dvdfds_matadata:
            export_manager.export(permission_dict, export_type='permission_dict')
            logger.info(
                f'Successfully crawled permission metadata for {count_key(permission_dict)} datasets in total.'
            )
            export_manager.export(ds_dict, 'pid_dict')

    meta_dict = parsing.add_permission_info(meta_dict, permission_dict)

    if meta_dict:
        export_manager.export(meta_dict, 'ds_metadata')
        logger.info(
            f'Successfully crawled {count_key(meta_dict)} metadata of dataset representation and file in total.'
        )

    if options.empty_dv:
        export_manager.export(empty_dv_dict, 'empty_dv')

    if options.spreadsheet:
        csv_file_path, csv_file_checksum = Spreadsheet(config).make_csv_file(meta_dict)
        export_manager.add_spreadsheet_record(csv_file_path, csv_file_checksum)

    return (
        meta_dict,
        export_manager.get_tracking_data(),
        failed_metadata_uris,
        pid_dict_dd,
        parsing.collections_tree_flatten,
    )
