import urllib.error
from unittest.mock import mock_open

import pandas as pd
import pytest
from pytest_mock import MockerFixture
from mock import call

import nlpland.data.dataset as dataset
from nlpland.constants import MISSING_PAPERS

df_missing = pd.DataFrame([["c", "http://abc/c.pdf"]])


@pytest.fixture()
def getenv(mocker: MockerFixture):
    yield mocker.patch("os.getenv", return_value="papers")


@pytest.fixture()
def readcsv(mocker: MockerFixture):
    yield mocker.patch("pandas.read_csv", return_value=df_missing)


@pytest.fixture()
def makedirs(mocker: MockerFixture):
    yield mocker.patch("os.makedirs")


@pytest.fixture()
def urlretrieve(mocker: MockerFixture):
    yield mocker.patch("urllib.request.urlretrieve")


def test_download_papers(getenv, readcsv, makedirs, urlretrieve):
    df_papers = pd.DataFrame(
        {
            "AA year of publication": [2010, 2011],
            "NS venue name": ["ACL", "EMNLP"],
            "AA url": ["https://www.aclweb.org/anthology/a", "https://abc/b.pdf"],
        },
        index=["a", "b"],
    )
    dataset.download_papers(df_papers)
    getenv.assert_called_with("PATH_PAPERS")
    readcsv.assert_called()

    makedirs_calls = [
        call("papers/2010/ACL", exist_ok=True),
        call("papers/2011/EMNLP", exist_ok=True),
    ]
    makedirs.assert_has_calls(makedirs_calls)
    urlretrieve_calls = [
        call("https://www.aclweb.org/anthology/a.pdf", "papers/2010/ACL/a.pdf"),
        call("https://abc/b.pdf", "papers/2011/EMNLP/b.pdf"),
    ]
    urlretrieve.assert_has_calls(urlretrieve_calls)


def test_download_papers_skip_request(mocker: MockerFixture, getenv, readcsv, makedirs, urlretrieve):
    df_paper = pd.DataFrame(
        {
            "AA year of publication": [2010],
            "NS venue name": ["EMNLP"],
            "AA url": ["http://abc/a.pdf"],
        },
        index=["a"],
    )
    df_paper.index = ["c"]
    dataset.download_papers(df_paper)
    urlretrieve.assert_not_called()

    mocker.patch("os.path.isfile", side_effect=[True])
    df_paper.index = ["a"]
    dataset.download_papers(df_paper)
    urlretrieve.assert_not_called()


def test_download_papers_error(mocker: MockerFixture, getenv, readcsv, makedirs):
    df_paper = pd.DataFrame(
        {
            "AA year of publication": [2010],
            "NS venue name": ["EMNLP"],
            "AA url": ["http://abc/a.pdf"],
        },
        index=["a"],
    )
    urlretrieve = mocker.patch(
        "urllib.request.urlretrieve",
        side_effect=[urllib.error.HTTPError("http://url.com", 404, "", {}, None)],
    )
    open_ = mock_open(mock=mocker.patch("builtins.open"))

    dataset.download_papers(df_paper)

    urlretrieve.assert_called_once()
    open_.assert_called_once_with(MISSING_PAPERS, "a+", encoding="utf-8")
    open_().write.assert_called_once_with("a\thttp://abc/a.pdf\n")
