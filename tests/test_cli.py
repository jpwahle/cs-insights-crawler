from click.testing import CliRunner

from nlpland import cli


def test_test() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.test, catch_exceptions=False)
    assert result.exit_code == 0
