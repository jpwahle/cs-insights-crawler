from typing import Dict, List

import numpy as np
import pandas as pd
import pytest
from pytest_mock import MockerFixture

from nlpland.constants import (
    ABSTRACT_SOURCE_ANTHOLOGY,
    ABSTRACT_SOURCE_RULE,
    COLUMN_ABSTRACT,
    COLUMN_ABSTRACT_SOURCE,
    FILTER_DATATYPES,
)
from nlpland.data import filter as filter_


def test_mask_data():
    df_papers = pd.DataFrame(
        {
            "AA title": ["title1", "title2", "title3"],
            COLUMN_ABSTRACT: ["abstract1", "abstract2", np.nan],
            COLUMN_ABSTRACT_SOURCE: [
                ABSTRACT_SOURCE_RULE,
                ABSTRACT_SOURCE_ANTHOLOGY,
                np.nan,
            ],
        }
    )

    df_result = filter_.mask_data(df_papers.copy(), "all")
    assert df_result.equals(df_papers)

    df_result = filter_.mask_data(df_papers.copy(), "titles")
    assert df_result.drop(COLUMN_ABSTRACT, axis=1).equals(df_papers.drop(COLUMN_ABSTRACT, axis=1))
    assert df_result[COLUMN_ABSTRACT].isna().values.any()

    df_result = filter_.mask_data(df_papers.copy(), "abstracts")
    assert df_result.drop("AA title", axis=1).equals(df_papers.drop("AA title", axis=1))
    assert df_result["AA title"].isna().values.any()

    df_result = filter_.mask_data(df_papers.copy(), "abstracts-rule")
    assert df_result.drop(["AA title", COLUMN_ABSTRACT], axis=1).equals(
        df_papers.drop(["AA title", COLUMN_ABSTRACT], axis=1)
    )
    assert df_result["AA title"].isna().values.any()
    assert df_result[COLUMN_ABSTRACT].equals(pd.Series(["abstract1", np.nan, np.nan]))

    df_result = filter_.mask_data(df_papers.copy(), "abstracts-anth")
    assert df_result.drop(["AA title", COLUMN_ABSTRACT], axis=1).equals(
        df_papers.drop(["AA title", COLUMN_ABSTRACT], axis=1)
    )
    assert df_result["AA title"].isna().values.any()
    assert df_result[COLUMN_ABSTRACT].equals(pd.Series([np.nan, "abstract2", np.nan]))


@pytest.mark.parametrize(
    "filters, second_df, expected",
    [
        ({"venues": "ACL"}, False, 0),
        ({"year": 2010}, False, 1),
        ({"min_year": 2006}, False, 1),
        ({"min_year": 2005, "year": 2010}, False, 1),
        ({"max_year": 2007}, False, 0),
        ({"author": "last, first"}, False, 0),
        ({"fauthor": "last2, first2"}, False, 1),
        ({"venues": "ACL", "venues2": "EMNLP"}, False, 0),
        ({"venues": "ACL", "venues2": "EMNLP"}, True, 1),
    ],
)
def test_get_filtered_df(
    mocker: MockerFixture,
    filters: Dict[str, FILTER_DATATYPES],
    second_df: bool,
    expected: int,
):
    df_papers = pd.DataFrame(
        {
            "NS venue name": ["ACL", "EMNLP"],
            "AA year of publication": [2005, 2010],
            "AA authors list": ["last, first and last2, first2", "last2, first2"],
            "AA first author full name": ["last, first", "last2, first2"],
        }
    )
    load = mocker.patch("nlpland.data.dataset.load_dataset", return_value=df_papers)

    df_result = filter_.get_filtered_df(filters, second_df=second_df)
    assert df_result.equals(df_papers.iloc[[expected], :])
    load.assert_called_once_with(False)


def test_get_filtered_df_call_mask(mocker: MockerFixture):
    df_papers = pd.DataFrame({"NS venue name": ["ACL", "EMNLP"]})
    load = mocker.patch("nlpland.data.dataset.load_dataset", return_value=df_papers)
    mask = mocker.patch("nlpland.data.filter.mask_data")

    filter_.get_filtered_df({"data": "titles"}, second_df=False)
    load.assert_called_once_with(False)
    mask.assert_called_once_with(df_papers, str("titles"))


@pytest.mark.parametrize(
    "attributes, expected",
    [("test, test1", ["test", "test1"]), ("test,test1", ["test", "test1"])],
)
def test_attribute_to_list(attributes: str, expected: List[str]):
    assert filter_.attributes_to_list(attributes) == expected


@pytest.mark.parametrize(
    "filters, second_df, expected",
    [
        ({"a": 3, "b": "test"}, False, [3, "test"]),
        ({"a": 3, "b": "test", "c": True}, False, [3, "test", "c"]),
        ({"a": 3, "b": "test", "c": False}, False, [3, "test"]),
        ({"a": 3, "b2": "test"}, False, [3]),
        ({"a": 3, "b2": "test"}, True, ["test"]),
    ],
)
def test_category_names(
    filters: Dict[str, FILTER_DATATYPES],
    second_df: bool,
    expected: List[FILTER_DATATYPES],
):
    assert filter_.category_names(filters, second_df=second_df) == expected
