import asyncio
from dataclasses import dataclass
from typing import Any

import typer
from loguru import logger

from dvmeta.cli.options import TyperOptions
from dvmeta.cli.validation import validate_api_token_presence
from dvmeta.cli.validation import validate_connection
from dvmeta.crawler.crawler import MetaDataCrawler
from dvmeta.crawler.utils import get_pids_from_search_response
from dvmeta.crawler.utils import merge_oaiore_to_meta_dict
from dvmeta.crawler.utils import merge_permission_to_meta_dict
from dvmeta.crawler.utils import parse_search_response
from dvmeta.custom_logging import CustomLogger
from dvmeta.dirmanager import DirManager
from dvmeta.exporter import ExportManager
from dvmeta.log_generation import write_to_log
from dvmeta.models.config import Config
from dvmeta.models.crawl_result import CrawlResult
from dvmeta.spreadsheet import Spreadsheet
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
    permission: bool = False
    failed: bool = False
    spreadsheet: bool = False
    metadata_source: str | None = None
    publication_status: str | None = None

    exporter: ExportManager | None = None
    skip_export: bool = False

    dataset_records: Any | None = None
    dataset_ids: list[str] | None = None

    permission_records: Any | None = None


@app.callback()
def main(
    ctx: typer.Context,
    auth: str = TyperOptions.auth,
    log: bool = TyperOptions.log,
    permission: bool = TyperOptions.permission,
    collection_alias: str = TyperOptions.collection_alias,
    version: str = TyperOptions.version,
    failed: bool = TyperOptions.failed,
    spreadsheet: bool = TyperOptions.spreadsheet,
    debug_log: bool = TyperOptions.debug_log,
    metadata_source: str = TyperOptions.metadata_source,
    publication_status: str = TyperOptions.publication_status,
    semaphore_limit: int = TyperOptions.semaphore_limit,
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
    config.semaphore_limit = semaphore_limit

    validate_api_token_presence(permission, config)

    auth_status = validate_connection(config)
    config.api_key = None if not auth_status else config.api_key

    state.config = config
    state.log = log
    state.permission = permission
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

    crawler = state.crawler
    dataset_ids = state.dataset_ids
    pids = list(get_pids_from_search_response(state.dataset_records).values())

    async def _fetch_all() -> tuple[dict, dict]:
        return await asyncio.gather(
            crawler.get_dataset_metadata(dataset_ids),
            crawler.get_oaiore_metadata(pids),
        )

    meta_dict, oaiore_metadata = asyncio.run(_fetch_all())

    # Merge OAI-ORE metadata into the meta_dict
    state.crawl_result.meta_dict = merge_oaiore_to_meta_dict(meta_dict, oaiore_metadata)

    if not state.skip_export:
        state.exporter.export(state.crawl_result.meta_dict, export_type='ds_metadata')

    if state.log:
        state.timestamps.end_time = get_current_time()
        write_to_log(state.config, state.timestamps, state.crawl_result)

    logger.info(
        f'Dataset metadata crawl for collection "{state.config.collection_alias}" completed. Crawled {len(state.crawl_result.meta_dict)} datasets.'
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

    if not state.skip_export:
        state.exporter.export(state.permission_records, export_type='permission')

    logger.info(
        f'Permission metadata for collection "{state.config.collection_alias}" completed. Crawled {len(state.permission_records)} records.'
    )


@app.command()
def export_spreadsheet(ctx: typer.Context):
    """Step 5: export to spreadsheet."""
    state = get_state(ctx)

    assert state.crawl_result is not None
    assert state.crawl_result.meta_dict is not None
    assert state.config is not None

    spreadsheet = Spreadsheet(state.config)
    spreadsheet.make_csv_file(state.crawl_result.meta_dict)


@app.command()
def run_all(ctx: typer.Context):
    """Run all steps in sequence."""
    state = get_state(ctx)
    state.skip_export = True

    search(ctx)
    crawl_metadata(ctx)
    crawl_permission(ctx)

    assert state.crawl_result is not None
    assert state.permission_records is not None
    assert state.exporter is not None
    state.crawl_result.meta_dict = merge_permission_to_meta_dict(state.crawl_result.meta_dict, state.permission_records)
    state.exporter.export(state.crawl_result.meta_dict, export_type='ds_metadata')
    export_spreadsheet(ctx)


if __name__ == '__main__':
    app()
