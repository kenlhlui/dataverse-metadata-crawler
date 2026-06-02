"""Module to generate log file."""

from pathlib import Path

from jinja2 import Template
from loguru import logger

from dvmeta.dirmanager import DirManager
from dvmeta.models.config import Config
from dvmeta.models.crawl_result import CrawlResult
from dvmeta.timestamp import Timestamps
from dvmeta.timestamp import get_display_time
from dvmeta.timestamp import get_elapsed_time
from dvmeta.timestamp import get_file_timestamp
from dvmeta.utils import count_key


def write_to_log(  # noqa:  PLR0913
    config: Config,
    timestamps: Timestamps,
    crawl_result: CrawlResult,
) -> None:
    """Write the crawl log to a file.

    Args:
        config (dict): Configuration dictionary
        timestamps (Timestamps): Timestamps object containing start and end times
        crawl_result (CrawlResult): Result object containing all crawled data

    Returns:
        str: Path to the log file
    """
    report = Template(read_template())
    rendered = report.render(
        config=config,
        start_time_display=get_display_time(timestamps.start_time),
        end_time_display=get_display_time(timestamps.end_time),
        elapsed_time=get_elapsed_time(timestamps.start_time, timestamps.end_time),
        meta_dict=count_key(crawl_result.meta_dict),
        collections_tree_flatten=count_key(crawl_result.collections_tree_flatten),
        pid_dict_dd=count_key(crawl_result.pid_dict_dd),
        failed_metadata_ids=count_key(crawl_result.failed_metadata_uris),
        # file_num=count_files_size(crawl_result.meta_dict)[0],
        # file_size=count_files_size(crawl_result.meta_dict)[1],
        json_file_checksum_dict=crawl_result.export_data,
    )

    log_file_path = f'{DirManager().log_files_dir()}/log_{get_file_timestamp()}.txt'

    with Path(log_file_path).open('w', encoding='utf-8') as file:
        file.write(rendered)

    return logger.info(f'The crawl log is saved at: {log_file_path}')


def read_template() -> str:
    """Read the log template file from res directory.

    Returns:
        str: Content of the template file as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    with Path('res/log_template.txt').open(encoding='utf-8') as file:
        return file.read()
