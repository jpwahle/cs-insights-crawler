import os
import urllib.error
from collections import defaultdict
from unittest.mock import mock_open

import numpy as np
import pandas as pd
import pytest
from mock import call
from pytest_mock import MockerFixture

from nlpland.data import dataset
from nlpland.constants import (
    ABSTRACT_SOURCE_ANTHOLOGY,
    ABSTRACT_SOURCE_RULE,
    COLUMN_ABSTRACT,
    COLUMN_ABSTRACT_SOURCE,
    MISSING_PAPERS,
)

df_missing = pd.DataFrame([["c", "http://abc/c.pdf"]])


@pytest.fixture()
def mock_env_papers(monkeypatch):
    monkeypatch.setenv("PATH_PAPERS", "papers")


@pytest.fixture()
def readcsv(mocker: MockerFixture):
    yield mocker.patch("pandas.read_csv", return_value=df_missing)


@pytest.fixture()
def makedirs(mocker: MockerFixture):
    yield mocker.patch("os.makedirs")


@pytest.fixture()
def urlretrieve(mocker: MockerFixture):
    yield mocker.patch("urllib.request.urlretrieve")


def test_download_papers(mock_env_papers, readcsv, makedirs, urlretrieve):
    df_papers = pd.DataFrame(
        {
            "AA year of publication": [2010, 2011],
            "NS venue name": ["ACL", "EMNLP"],
            "AA url": ["https://www.aclweb.org/anthology/a", "https://abc/b.pdf"],
        },
        index=["a", "b"],
    )
    dataset.download_papers(df_papers)
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


def test_download_papers_skip_request(
    mocker: MockerFixture, mock_env_papers, readcsv, makedirs, urlretrieve
):
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

    mocker.patch("os.path.isfile", return_value=True)
    df_paper.index = ["a"]
    dataset.download_papers(df_paper)
    urlretrieve.assert_not_called()


def test_download_papers_error(
    mocker: MockerFixture, mock_env_papers, readcsv, makedirs
):
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
        side_effect=[urllib.error.HTTPError("http://url.com", 404, "", {"": ""}, None)],
    )
    open_ = mock_open(mock=mocker.patch("builtins.open"))

    dataset.download_papers(df_paper)

    urlretrieve.assert_called_once()
    open_.assert_called_once_with(MISSING_PAPERS, "a+", encoding="utf-8")
    open_().write.assert_called_once_with("a\thttp://abc/a.pdf\n")


def test_save_load_dataset(monkeypatch):
    df_paper = pd.DataFrame(
        {
            "NS venue name": [np.nan],
            "AA url": ["http://abc/a.pdf"],
        },
        index=["a"],
    )
    path_old = "tests/old.txt"
    path_new = "tests/new.txt"
    monkeypatch.setenv("PATH_DATASET", path_old)
    monkeypatch.setenv("PATH_DATASET_EXPANDED", path_new)

    df_paper.to_csv(os.getenv("PATH_DATASET"), sep="\t", na_rep="NA")
    df_paper_loaded = dataset.load_dataset(original_dataset=True)
    assert df_paper_loaded.equals(df_paper)

    df_paper_loaded.at["a", COLUMN_ABSTRACT] = "test"
    # df_paper_loaded[COLUMN_ABSTRACT] = df_paper_loaded[COLUMN_ABSTRACT].replace([])
    dataset.save_dataset(df_paper_loaded)
    df_paper_loaded2 = dataset.load_dataset(original_dataset=False)
    assert df_paper_loaded2.equals(df_paper_loaded)

    os.remove(path_old)
    os.remove(path_new)


@pytest.mark.parametrize(
    "text, possible_strings, earliest_pos, earliest_string",
    [
        ("1232", ["2", "3"], 1, "2"),
        ("cb ad", ["a", "c"], 0, "c"),
    ],
)
def test_determine_earliest_string(
    text, possible_strings, earliest_pos, earliest_string
):
    assert (earliest_pos, earliest_string) == dataset.determine_earliest_string(
        text, possible_strings
    )


def test_print_results_extract_abstracts_rulebased(capfd):
    duration = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    count_dict: dict = defaultdict(int)
    count_dict["searched"] += 3

    dataset.print_results_extract_abstracts_rulebased(count_dict, duration)
    capture = capfd.readouterr()
    assert "3 abstracts searched" in capture.out
    assert "05m 06s" in capture.out


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Abstract\ntext\n\n1 Introduction", "text"),
        ("ABSTRACT\ntext\n\n1. Introduction", "text"),
        ("Abstract text\nKeywords:", "text\n"),
        ("A b s t r a c t\ntext\nKeywords :", "text\n"),
        ("Abstract\ntext\n\nIntroduction\n\n", "text"),
    ],
)
def test_helper_abstracts_rulebased(mocker, text, expected):
    df_paper = pd.DataFrame(
        {"NS venue name": ["ACL"], "AA year of publication": [2010]}, index=["a"]
    )

    mocker.patch("os.path.isfile", return_value=True)
    mocker.patch("tika.parser.from_file", return_value={"content": text})

    count_dict: dict = defaultdict(int)
    index = df_paper.index[0]
    df_result = dataset.helper_abstracts_rulebased(
        index, count_dict, "papers", df_paper
    )
    assert df_result.at[index, COLUMN_ABSTRACT] == expected


@pytest.mark.parametrize(
    "overwrite, calls",
    [(False, 1), (True, 2)],
)
def test_extract_abstracts_rulebased(mocker, monkeypatch, overwrite, calls):
    df_full = pd.DataFrame({})
    df_return = pd.DataFrame({}, index=["z"])
    df_select = pd.DataFrame(
        {
            COLUMN_ABSTRACT_SOURCE: [
                ABSTRACT_SOURCE_RULE,
                ABSTRACT_SOURCE_ANTHOLOGY,
                ABSTRACT_SOURCE_RULE,
            ],
            COLUMN_ABSTRACT: ["text", "text", None],
        },
        index=["a", "b", "c"],
    )

    monkeypatch.setenv("PATH_PAPERS", "papers")
    init = mocker.patch("tika.initVM")
    save = mocker.patch("nlpland.data.dataset.save_dataset")
    helper = mocker.patch(
        "nlpland.data.dataset.helper_abstracts_rulebased", return_value=df_return
    )
    mocker.patch("nlpland.data.dataset.print_results_extract_abstracts_rulebased")

    dataset.extract_abstracts_rulebased(df_select, df_full, overwrite_rule=overwrite)
    init.assert_called_once()
    save.assert_called_once_with(df_return)
    assert helper.call_count == calls


def test_extract_abstracts_anthology(monkeypatch):
    xml1 = """
    <collection id="2010.abc">
      <volume id="1">
        <paper id="1">
          <abstract>In this paper ...</abstract>
          <url>2010.abc.1</url>
        </paper>
        <paper id="2">
        </paper>
      </volume>
    </collection>"""
    xml2 = """
    <collection id="L01">
      <volume id="1">
        <paper id="1">
          <abstract>In the field ...</abstract>
          <url>http://abc/a.pdf</url>
        </paper>
      </volume>
    </collection>"""
    file1 = "tests/xml1.xml"
    file2 = "tests/xml2.xml"
    with open(file1, "w+", encoding="utf-8") as file:
        file.write(xml1)
    with open(file2, "w+", encoding="utf-8") as file:
        file.write(xml2)

    index = ["2010.abc.1", "L01-1-1"]
    monkeypatch.setenv("PATH_ANTHOLOGY", "tests")
    df_papers = pd.DataFrame({}, index=index)

    dataset.extract_abstracts_anthology(df_papers)
    expected = pd.Series(["In this paper ...", "In the field ..."], index=index)
    assert df_papers[COLUMN_ABSTRACT].equals(expected)

    os.remove(file1)
    os.remove(file2)
