"""This module provides the entry points for CLI commands."""
import logging
import time
from typing import Any

import click
from click.testing import CliRunner

import nlpland.process.continous as continous_


@click.group()
def cli() -> None:
    """Executed before every command."""
    pass


@cli.command()
@continous_.filter_options
def continous(**kwargs: Any) -> None:
    """Download, extract, and store data extracted data from DBLP release and full-text pdfs
    to NLP-Land-backend

    Args:
        **kwargs(Any): Command line arguments for the process.
    """
    while True:
        continous_.main(**kwargs)
        time.sleep(10 * 24 * 60 * 60)  # 10 days


@cli.command()
def batch(**kwargs: Any) -> None:
    """Download, extract, and store extracted data from DBLP release and full-text pdfs locally.

    Args:
        **kwargs(Any): Command line arguments for the process.
    """
    pass


if __name__ == "__main__":
    """Main routine for the CLI. Only for debugging purposes"""
    runner = CliRunner()
    continous(
        [
            "--verbose",
            "--store_local",
            "--crawler_overwrite_pdf_cache_dir",
            "--crawler_shuffle_requests",
        ]
    )  # ["--dblp_use_filters"]
