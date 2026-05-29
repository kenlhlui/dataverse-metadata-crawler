# """The command line interface for dvmeta."""

# import asyncio

# import typer
# from loguru import logger

# from dvmeta.cli.options import TyperOptions
# from dvmeta.cli.validation import validate_api_token_presence
# from dvmeta.cli.validation import validate_basic_input
# from dvmeta.cli.validation import validate_collection_data
# from dvmeta.cli.validation import validate_collections_tree
# from dvmeta.cli.validation import validate_connection
# from dvmeta.cli.validation import validate_spreadsheet_option
# from dvmeta.cli.workers import CrawlOptions
# from dvmeta.cli.workers import run_crawl
# from dvmeta.crawler import MetaDataCrawler
# from dvmeta.custom_logging import CustomLogger
# from dvmeta.dirmanager import DirManager
# from dvmeta.log_generation import write_to_log
# from dvmeta.timestamp import Timestamps
# from dvmeta.timestamp import get_current_time
# from dvmeta.utils import load_env
# from dvmeta.utils import update_config_with_collection_data


# app = typer.Typer()


# @app.command()
# def main(
#     auth: str = TyperOptions.auth,
#     log: bool = TyperOptions.log,
#     dvdfds_matadata: bool = TyperOptions.dvdfds_metadata,
#     permission: bool = TyperOptions.permission,
#     collection_alias: str = TyperOptions.collection_alias,
#     version: str = TyperOptions.version,
#     empty_dv: bool = TyperOptions.empty_dv,
#     failed: bool = TyperOptions.failed,
#     spreadsheet: bool = TyperOptions.spreadsheet,
#     debug_log: bool = TyperOptions.debug_log,
# ):
#     """A Python CLI tool for extracting and exporting metadata from Dataverse repositories to JSON and CSV formats."""
#     CustomLogger.setup_logging(DirManager().log_files_dir()) if debug_log else CustomLogger.setup_logging()

#     timestamps = Timestamps(start_time=get_current_time())

#     config = load_env()
#     config.collection_alias = collection_alias
#     config.version = version
#     config.api_key = auth if auth else config.api_key

#     validate_spreadsheet_option(spreadsheet, dvdfds_matadata)
#     validate_basic_input(dvdfds_matadata, permission)
#     validate_api_token_presence(permission, config)

#     auth_status = validate_connection(config)
#     config.api_key = None if not auth_status else config.api_key

#     metadata_crawler = MetaDataCrawler(config)

#     collections_tree = validate_collections_tree(metadata_crawler.get_collections_tree(collection_alias))
#     collection_data = validate_collection_data(collections_tree)
#     config = update_config_with_collection_data(config, collection_data)

#     logger.info('Starting the main crawling function...')

#     options = CrawlOptions(
#         dvdfds_matadata=dvdfds_matadata,
#         permission=permission,
#         empty_dv=empty_dv,
#         spreadsheet=spreadsheet,
#         failed=failed,
#     )
#     crawl_result = asyncio.run(run_crawl(config, metadata_crawler, collections_tree, options))

#     timestamps.end_time = get_current_time()

#     if log:
#         write_to_log(
#             config,
#             timestamps,
#             crawl_result,
#         )

#     logger.info('✅ Crawling process completed successfully.')


# if __name__ == '__main__':
#     app()
