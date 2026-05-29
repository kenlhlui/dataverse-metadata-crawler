"""Typer options with types and defaults for the CLI application."""

import typer

from dvmeta.cli.validation import validate_version_type


class TyperOptions:
    """Helper class for Typer options with types and defaults."""

    auth: str = typer.Option(
        None,
        '--auth',
        '-a',
        help='Authentication token to access the dataverse repository',
        hide_input=True,
        envvar='API_KEY',
    )
    log: bool = typer.Option(True, '--log/--no-log', '-l', help='Output log file')
    dvdfds_metadata: bool = typer.Option(
        False, '--dvdfds_metadata', '-d', help='Output JSON file of metadata of dataverse, dataset and datafiles'
    )
    permission: bool = typer.Option(
        False,
        '--permission',
        '-p',
        help='Output JSON file that stores permission metadata of all datasets in the repository',
    )
    collection_alias: str = typer.Option(
        ...,
        '--collection_alias',
        '-c',
        help='Name of the collection to crawl',
        allow_dash=True,
        prompt_required=True,
    )
    version: str = typer.Option(
        ...,
        '--version',
        '-v',
        help=(
            'The dataset version to crawl. Options are:\n'
            "  'draft' - the draft version, if any\n"
            "  'latest' - either a draft (if exists) or the latest published version\n"
            "  'latest-published' - the latest published version\n"
            "  'x.y' - a specific version, where x is the major version number and y is the minor version number\n"
            "  'x' - same as 'x.0'"
        ),
        prompt_required=True,
        callback=validate_version_type,
    )
    empty_dv: bool = typer.Option(
        False,
        '--emptydv',
        '-e',
        help='Output JSON file that stores all dataverses that does have contain datasets (but might include child dataverses and their child dataverses might have datasets)',
    )
    failed: bool = typer.Option(
        False, '--failed', '-f', help='Output JSON file that stores dataverses/datasets failed to be crawled'
    )
    spreadsheet: bool = typer.Option(
        False,
        '--spreadsheet',
        '-s',
        help='Output a CSV file of the metadata of datasets',
    )
    debug_log: bool = typer.Option(
        False,
        '--debug-log',
        '-debug',
        help='Enable debug logging. This will create a debug log file in the log_files directory.',
    )
    metadata_source: str = typer.Option(
        None,
        '--metadata-source',
        '-m',
        help='The source of the metadata to crawl. This option can be used to filter harvested datasets.',
    )
