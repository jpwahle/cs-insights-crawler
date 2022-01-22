from click.testing import CliRunner

from nlpland import cli


def test_continous() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.continous, catch_exceptions=False)
    assert result.exit_code == 0


def test_scheduled() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.continous, catch_exceptions=False)
    assert result.exit_code == 0
