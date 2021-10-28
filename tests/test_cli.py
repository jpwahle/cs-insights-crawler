from unittest.mock import MagicMock

import pandas as pd
import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from nlpland import cli

df_filtered = pd.DataFrame({"AA url": ["a"]})
df_full = pd.DataFrame({"AA url": ["a", "b"]})


@pytest.fixture
def filtered(mocker: MockerFixture) -> None:
    yield mocker.patch("nlpland.data.filter.get_filtered_df", return_value=df_filtered)


@pytest.fixture
def load(mocker: MockerFixture) -> None:
    yield mocker.patch("nlpland.data.dataset.load_dataset", return_value=df_full)


def test_download(mocker: MockerFixture, filtered: MagicMock) -> None:
    download = mocker.patch("nlpland.data.dataset.download_papers")

    runner = CliRunner()
    result = runner.invoke(cli.download, args=["--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    filtered.assert_called_once()
    assert filtered.call_args[0][0]["venues"] == "ACL"
    download.assert_called_once_with(df_filtered)


def test_extract(mocker: MockerFixture, filtered: MagicMock) -> None:
    load = mocker.patch("nlpland.data.dataset.load_dataset", return_value=df_full)
    rule = mocker.patch("nlpland.data.dataset.extract_abstracts_rulebased")
    anth = mocker.patch("nlpland.data.dataset.extract_abstracts_anthology")

    runner = CliRunner()
    result = runner.invoke(cli.extract, args=["test", "--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Unsupported mode 'test'" in result.output

    result = runner.invoke(cli.extract, args=["rule", "--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    filtered.assert_called_once()
    assert filtered.call_args[0][0]["venues"] == "ACL"
    rule.assert_called_once_with(df_filtered, df_full, overwrite_rule=False)

    result = runner.invoke(cli.extract, args=["anth"], catch_exceptions=False)
    assert result.exit_code == 0
    anth.assert_called_once_with(df_full)

    assert load.call_count == 3


def test_checkencode(mocker: MockerFixture, load: MagicMock) -> None:
    check = mocker.patch("nlpland.data.check.check_encoding_issues")

    runner = CliRunner()
    result = runner.invoke(cli.checkencode, catch_exceptions=False)
    assert result.exit_code == 0
    load.assert_called_once_with(False)
    check.assert_called_once_with(df_full)


def test_checkdataset(mocker: MockerFixture, load: MagicMock) -> None:
    check = mocker.patch("nlpland.data.check.check_dataset")

    runner = CliRunner()
    result = runner.invoke(cli.checkdataset, catch_exceptions=False)
    assert result.exit_code == 0
    load.assert_called_once_with(False)
    check.assert_called_once_with(df_full)


def test_checkpaper(mocker: MockerFixture) -> None:
    paper_path = "path"
    check = mocker.patch("nlpland.data.check.check_paper_parsing")

    runner = CliRunner()
    result = runner.invoke(cli.checkpaper, args=[paper_path], catch_exceptions=False)
    assert result.exit_code == 0
    check.assert_called_once_with(paper_path)


def test_countabstractsanth(mocker: MockerFixture) -> None:
    check = mocker.patch("nlpland.data.check.count_anthology_abstracts")

    runner = CliRunner()
    result = runner.invoke(cli.countabstractsanth, catch_exceptions=False)
    assert result.exit_code == 0
    check.assert_called_once()


def test_count(mocker: MockerFixture, filtered: MagicMock) -> None:
    count = mocker.patch("nlpland.modules.count.top_k_tokens", return_value=(3, 4))

    runner = CliRunner()
    result = runner.invoke(cli.count, args=["5", "--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    filtered.assert_called_once()
    assert filtered.call_args[0][0]["venues"] == "ACL"
    count.assert_called_once_with(5, df_filtered, "1")


def test_counts_time(mocker: MockerFixture, filtered: MagicMock) -> None:
    count = mocker.patch("nlpland.modules.count.counts_over_time")

    runner = CliRunner()
    result = runner.invoke(cli.counts_time, args=["5", "--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    filtered.assert_called_once()
    assert filtered.call_args[0][0]["venues"] == "ACL"
    count.assert_called_once_with(df_filtered, 5, "1", None, False, filtered.call_args[0][0])


def test_scatter(mocker: MockerFixture, filtered: MagicMock) -> None:
    df_y = pd.DataFrame({"AA url": ["b"]})
    df_x = pd.DataFrame({"AA url": ["a"]})
    filtered = mocker.patch("nlpland.data.filter.get_filtered_df", side_effect=[df_y, df_x])
    scatter = mocker.patch("nlpland.modules.scatter.plot_word_counts")

    runner = CliRunner()
    result = runner.invoke(cli.scatter, args=["--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    assert filtered.call_count == 2
    assert filtered.call_args[0][0]["venues"] == "ACL"
    scatter.assert_called_once_with(df_y, df_x, False, None, filtered.call_args[0][0])


def test_topic_train(mocker: MockerFixture, filtered: MagicMock) -> None:
    topic = mocker.patch("nlpland.modules.topic_model.topic")

    runner = CliRunner()
    result = runner.invoke(cli.topic_train, args=["5", "--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    filtered.assert_called_once()
    assert filtered.call_args[0][0]["venues"] == "ACL"
    topic.assert_called_once_with(df_filtered, 5, None)


def test_fasttext(mocker: MockerFixture, filtered: MagicMock) -> None:
    semantic = mocker.patch("nlpland.modules.semantic.semantic")

    runner = CliRunner()
    result = runner.invoke(cli.fasttext, args=["--venues", "ACL"], catch_exceptions=False)
    assert result.exit_code == 0
    filtered.assert_called_once()
    assert filtered.call_args[0][0]["venues"] == "ACL"
    semantic.assert_called_once_with(df_filtered, False, None)


def test_test() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.test, catch_exceptions=False)
    assert result.exit_code == 0
