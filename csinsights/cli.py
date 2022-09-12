"""This module provides the entry points for CLI commands."""
from datetime import datetime
from typing import Union

import click

from csinsights import process
from csinsights.types import AccessType


@click.group()
def cli() -> None:
    """Executed before every command."""
    pass


@cli.command()
@process.filter_options
def main(**kwargs: Union[str, bool, int, AccessType, datetime]) -> None:
    """Download, extract, and store data extracted data from DBLP release and full-text pdfs

    Args:
        **kwargs(Any): Command line arguments for the process.
    """
    process.main(**kwargs)
