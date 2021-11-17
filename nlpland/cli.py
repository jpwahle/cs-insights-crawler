"""This module provides the entry points for the CLI commands."""
import click
from click.testing import CliRunner
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli() -> None:
    """Executed before every command."""


if __name__ == "__main__":
    # this is for debugging via IDE

    runner = CliRunner()
    result = runner.invoke(count, args=["5"], catch_exceptions=False)
    # traceback.print_exception(*result.exc_info)
