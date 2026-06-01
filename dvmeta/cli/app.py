import asyncio
from dataclasses import dataclass
from typing import Any

import typer
from loguru import logger

from dvmeta.cli.options import TyperOptions
from dvmeta.cli.validation import validate_api_token_presence
from dvmeta.cli.validation import validate_basic_input
from dvmeta.cli.validation import validate_connection
from dvmeta.cli.validation import validate_spreadsheet_option
from dvmeta.crawl_result import CrawlResult
from dvmeta.crawler.new_crawler import MetaDataCrawler
from dvmeta.crawler.utils import parse_search_response
from dvmeta.custom_logging import CustomLogger
from dvmeta.dirmanager import DirManager
from dvmeta.exporter import ExportManager
from dvmeta.log_generation import write_to_log
from dvmeta.models import Config
from dvmeta.timestamp import Timestamps
from dvmeta.timestamp import get_current_time
from dvmeta.utils import load_env


app = typer.Typer()


@dataclass
class CLIState:
    config: Config | None = None
    timestamps: Timestamps | None = None
    crawler: MetaDataCrawler | None = None
    collections_tree: Any | None = None
    collection_data: Any | None = None
    crawl_result: CrawlResult | None = None
    log: bool = True
    dvdfds_metadata: bool = False
    permission: bool = False
    empty_dv: bool = False
    failed: bool = False
    spreadsheet: bool = False
    metadata_source: str | None = None
    publication_status: str | None = None

    exporter: ExportManager | None = None

    dataset_records: Any | None = None
    dataset_ids: list[str] | None = None

    permission_records: Any | None = None


@app.callback()
def main(
    ctx: typer.Context,
    auth: str = TyperOptions.auth,
    log: bool = TyperOptions.log,
    dvdfds_metadata: bool = TyperOptions.dvdfds_metadata,
    permission: bool = TyperOptions.permission,
    collection_alias: str = TyperOptions.collection_alias,
    version: str = TyperOptions.version,
    empty_dv: bool = TyperOptions.empty_dv,
    failed: bool = TyperOptions.failed,
    spreadsheet: bool = TyperOptions.spreadsheet,
    debug_log: bool = TyperOptions.debug_log,
    metadata_source: str = TyperOptions.metadata_source,
    publication_status: str = TyperOptions.publication_status,
):
    """Step 1: load config and validate inputs. Runs before every subcommand."""
    CustomLogger.setup_logging(DirManager().log_files_dir() if debug_log else None)

    state = CLIState()
    state.timestamps = Timestamps(start_time=get_current_time())

    config = load_env()
    config.collection_alias = collection_alias
    config.version = version
    config.api_key = auth if auth else config.api_key
    config.metadata_source = metadata_source

    validate_spreadsheet_option(spreadsheet, dvdfds_metadata)
    validate_basic_input(dvdfds_metadata, permission)
    validate_api_token_presence(permission, config)

    auth_status = validate_connection(config)
    config.api_key = None if not auth_status else config.api_key

    state.config = config
    state.log = log
    state.dvdfds_metadata = dvdfds_metadata
    state.permission = permission
    state.empty_dv = empty_dv
    state.failed = failed
    state.spreadsheet = spreadsheet
    state.metadata_source = config.metadata_source
    state.exporter = ExportManager()
    state.publication_status = publication_status
    ctx.obj = state


def get_state(ctx: typer.Context) -> CLIState:
    state = ctx.obj
    if state is None:
        msg = 'CLI state not initialized'
        raise typer.BadParameter(msg)
    return state


@app.command()
def search(ctx: typer.Context) -> None:
    """Step 2: search for datasets in the collection."""
    state = get_state(ctx)

    state.crawler = MetaDataCrawler(state.config)

    state.dataset_records = state.crawler.get_dataverse_ds_records(
        metadata_source=state.metadata_source, publication_status=state.publication_status
    )

    state.dataset_ids = parse_search_response(state.dataset_records)

    logger.info(
        f'Search for datasets in collection "{state.config.collection_alias}" completed. Found {len(state.dataset_ids)} datasets.'
    )


@app.command()
def crawl_metadata(ctx: typer.Context) -> None:
    """Step 3: crawl metadata."""
    state = get_state(ctx)

    if state.crawler is None:
        state.crawler = MetaDataCrawler(state.config)

    if state.dataset_records is None:
        # Run the search step if dataset_records is not already populated
        state.dataset_records = state.crawler.get_dataverse_ds_records(
            metadata_source=state.metadata_source, publication_status=state.publication_status
        )

    if state.dataset_ids is None:
        state.dataset_ids = parse_search_response(state.dataset_records)

    if state.crawl_result is None:
        state.crawl_result = CrawlResult()

    state.crawl_result.meta_dict = asyncio.run(state.crawler.get_dataset_metadata(state.dataset_ids))

    # TODO: Add the ORIORE crawling and path extraction here, and include it in the crawl_result

    state.exporter.export(state.crawl_result.meta_dict, export_type='ds_metadata')

    if state.log:
        state.timestamps.end_time = get_current_time()
        write_to_log(state.config, state.timestamps, state.crawl_result)

    logger.info(
        f'Metadata crawl for collection "{state.config.collection_alias}" completed. Crawled {len(state.crawl_result.meta_dict)} datasets.'
    )


@app.command()
def crawl_permission(ctx: typer.Context) -> None:
    """Step 4: crawl permissions."""
    state = get_state(ctx)

    if state.crawler is None:
        state.crawler = MetaDataCrawler(state.config)

    if state.dataset_records is None:
        # Run the search step if dataset_records is not already populated
        state.dataset_records = state.crawler.get_dataverse_ds_records(
            metadata_source=state.metadata_source, publication_status=state.publication_status
        )

    if state.dataset_ids is None:
        state.dataset_ids = parse_search_response(state.dataset_records)

    state.permission_records = asyncio.run(state.crawler.get_dataset_permissions(state.dataset_ids))

    logger.info(
        f'Permission crawl for collection {state.config.collection_alias} completed. Crawled {len(state.permission_records)} datasets.'
    )


@app.command()
def export_spreadsheet(ctx: typer.Context):
    """Step 5: export to spreadsheet."""
    state = get_state(ctx)

    if state.crawl_result is None:
        raise typer.BadParameter('Run crawl first, or load crawl_result from persistence.')

    # call your spreadsheet export function here
    typer.echo('Spreadsheet export completed.')


@app.command()
def write_log(ctx: typer.Context):
    """Step 6: write log."""
    state = get_state(ctx)

    if state.timestamps is None:
        raise typer.BadParameter('Missing timestamps.')

    if state.crawl_result is None:
        raise typer.BadParameter('Run crawl first, or load crawl_result from persistence.')

    state.timestamps.end_time = get_current_time()
    write_to_log(state.config, state.timestamps, state.crawl_result)
    typer.echo('Log written.')


@app.command()
def run_all(ctx: typer.Context):
    """Run all steps in sequence."""
    search(ctx)
    crawl_metadata(ctx)
    # crawl_permission(ctx)
    # export_spreadsheet(ctx)
    write_log(ctx)


if __name__ == '__main__':
    app()
