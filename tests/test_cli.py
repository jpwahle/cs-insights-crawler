import pandas as pd
from click.testing import CliRunner
from pytest_mock import MockerFixture

from nlpland import cli


def test_download(mocker: MockerFixture):
    df_paper = pd.DataFrame({"AA url": ["a"]})
    filtered = mocker.patch("nlpland.data.filter.get_filtered_df", return_value=df_paper)
    download = mocker.patch("nlpland.data.dataset.download_papers")

    runner = CliRunner()
    result = runner.invoke(cli.download, args=["--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    filtered.assert_called_once()
    assert filtered.call_args[0][0]["venues"] == "ACL"
    download.assert_called_once_with(df_paper)
