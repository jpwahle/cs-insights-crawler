"""This module provides the entry points for CLI commands."""
import logging
from typing import Any

import click
from click.testing import CliRunner

import nlpland.process.continous as continous_

logger = logging.getLogger("nlp-land-crawler")


@click.group()
def cli() -> None:
    """Executed before every command."""


@cli.command()
@continous_.filter_options
def continous(**kwargs: Any) -> None:
    """Download the papers that match the given filters.

    Args:
        **kwargs(Any): Command line arguments for the process.
    """
    continous_.main(**kwargs)


if __name__ == "__main__":
    """Main routine for the CLI. Only for debugging purposes"""
    runner = CliRunner()
    continous(["--use_authors", "--use_affiliations"])
