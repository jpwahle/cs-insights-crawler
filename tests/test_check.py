import pytest
import nlpland.data.check as check_
import pandas as pd
from nlpland.constants import (
    ABSTRACT_SOURCE_RULE,
    ABSTRACT_SOURCE_ANTHOLOGY,
    COLUMN_ABSTRACT,
    COLUMN_ABSTRACT_SOURCE,
)
import os


def test_print_null_values(capfd):
    test_df = pd.DataFrame({"col": ["1", "2", "34", "2", None, pd.NA]})
    print(type(capfd))
    check_.print_null_values(test_df["col"])
    capture = capfd.readouterr()
    assert "2" in capture.out
    assert "5" not in capture.out


def test_print_possible_values(capfd):
    test_df = pd.DataFrame({"col": ["1", "2", "34", "2", None, pd.NA]})
    check_.print_possible_values(test_df["col"])
    capture = capfd.readouterr()
    assert "1" in capture.out
    assert "2" in capture.out
    assert "34" in capture.out
    assert "5" not in capture.out
    assert "None" not in capture.out
    assert "NA" not in capture.out


def test_print_abstracts_per_year(capfd):
    test_df = pd.DataFrame(
        {
            COLUMN_ABSTRACT: ["1", "2", "34", "2", None, pd.NA],
            COLUMN_ABSTRACT_SOURCE: [
                ABSTRACT_SOURCE_RULE,
                ABSTRACT_SOURCE_ANTHOLOGY,
                ABSTRACT_SOURCE_ANTHOLOGY,
                ABSTRACT_SOURCE_ANTHOLOGY,
                None,
                None,
            ],
            "AA year of publication": [2000, 2001, 2000, 2003, 2000, 2000],
            "AA url": ["", "", "", "", "", ""],
        }
    )
    check_.print_abstracts_per_year(test_df)
    capture = capfd.readouterr()
    assert "1" in capture.out
    assert "2" in capture.out
    assert "3" in capture.out
    assert "4" in capture.out
    assert "6" in capture.out
    assert "66.67%" in capture.out


def test_check_dataset(mocker):
    test_df = pd.DataFrame(
        {
            COLUMN_ABSTRACT: ["1"],
            COLUMN_ABSTRACT_SOURCE: [ABSTRACT_SOURCE_RULE],
            "AA year of publication": [2000],
            "GS year of publication": [2000],
            "AA url": [""],
            "NS venue name": ["ACL"],
            "AA venue code": ["acl"],
            "AA first author full name": ["Jan"],
        }
    )
    null = mocker.patch("nlpland.data.check.print_null_values")
    unique = mocker.patch("nlpland.data.check.print_possible_values")
    year = mocker.patch("nlpland.data.check.print_abstracts_per_year")
    check_.check_dataset(test_df)

    null.assert_called()
    unique.assert_called()
    year.assert_called_once()


def test_check_encoding_issues(capfd):
    test_df = pd.DataFrame(
        {
            "AA year of publication": [2000, 2000, 2000, 2001, 2001],
            "NS venue name": ["ACL", "ACL", "ACL", "ACL", "ACL"],
            COLUMN_ABSTRACT: ["���", "��", "", "�", ""],
        }
    )
    check_.check_encoding_issues(test_df)
    capture = capfd.readouterr()
    assert "3" in capture.out


def test_check_paper_parsing(mocker, capfd):
    text = "Hallo Welt!"
    paper_path = "hello.pdf"
    parser = mocker.patch("tika.parser.from_file", return_value={"content": "\n" + text})

    check_.check_paper_parsing(paper_path)
    capture = capfd.readouterr()
    assert text in capture.out
    parser.assert_called_once_with(paper_path)


def test_count_anthology_abstracts(mocker, capfd):
    dir_name = "tmp_xml"
    mocker.patch("os.getenv", return_value=dir_name)

    os.makedirs(dir_name, exist_ok=True)

    xml1 = """
    <collection id="2007.abc">
      <volume id="1">
        <paper id="1">
          <abstract>In this paper ...</abstract>
        </paper>
        <paper id="2">
        </paper>
      </volume>
    </collection>"""
    xml2 = """
    <collection id="2008.abc">
      <volume id="1">
        <paper id="1">
          <abstract>In this paper ...</abstract>
        </paper>
      </volume>
    </collection>"""
    txt = """
    <collection id="2007.abc">
      <volume id="1">
        <paper id="1">
          <abstract>In this paper ...</abstract>
        </paper>
      </volume>
    </collection>"""

    with open(dir_name + "/xml1.xml", "w+", encoding="utf-8") as file:
        file.write(xml1)
    with open(dir_name + "/xml2.xml", "w+", encoding="utf-8") as file:
        file.write(xml2)
    with open(dir_name + "/text.txt", "w+", encoding="utf-8") as file:
        file.write(txt)

    check_.count_anthology_abstracts()
    capture = capfd.readouterr()
    assert "3 papers" in capture.out
    assert "2 abstracts" in capture.out

    os.remove(dir_name + "/xml1.xml")
    os.remove(dir_name + "/xml2.xml")
    os.remove(dir_name + "/text.txt")
    os.rmdir(dir_name)
