"""Module to generate log file."""

from pathlib import Path

from jinja2 import Template
from loguru import logger

from dvmeta.models.config import Config
from dvmeta.models.crawl_result import CrawlResult
from dvmeta.services.dir_manager import DirManager
from dvmeta.services.dir_manager import ExportDir
from dvmeta.services.timestamp import Timestamps
from dvmeta.services.timestamp import get_display_time
from dvmeta.services.timestamp import get_elapsed_time
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import count_key
from dvmeta.services.utils import get_collection_files_count
from dvmeta.services.utils import get_collection_files_size


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
        crawl_result=crawl_result,
        start_time_display=get_display_time(timestamps.start_time),
        end_time_display=get_display_time(timestamps.end_time),
        elapsed_time=get_elapsed_time(timestamps.start_time, timestamps.end_time),
        ds_metadata_num=count_key(crawl_result.meta_dict),
        pid_dict_dd=count_key(crawl_result.pid_dict_dd),
        permission_record_num=count_key(crawl_result.permission_dict),
        file_num=get_collection_files_count(crawl_result.meta_dict),
        file_size=get_collection_files_size(crawl_result.meta_dict),
        json_file_checksum_dict=crawl_result.export_data,
    )

    log_file_path = f'{DirManager().get_dir(ExportDir.LOG)}/report_{get_file_timestamp()}.txt'

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
