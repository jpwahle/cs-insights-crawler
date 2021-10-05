from typing import Callable, Dict, List

import click
import numpy as np
import pandas as pd

import nlpland.data.dataset as dataset_
from nlpland.constants import (ABSTRACT_SOURCE_ANTHOLOGY, ABSTRACT_SOURCE_RULE,
                               COLUMN_ABSTRACT, COLUMN_ABSTRACT_SOURCE,
                               FILTER_DATATYPES)


def df_filter_options(function: Callable, second_df: bool = False):
    if second_df:
        sec = "2"
    else:
        sec = ""
    function = click.option('--venues' + sec)(function)
    function = click.option('--year' + sec, type=int)(function)
    function = click.option('--min-year' + sec, type=int)(function)
    function = click.option('--max-year' + sec, type=int)(function)
    function = click.option('--author' + sec)(function)
    function = click.option('--fauthor' + sec)(function)
    function = click.option('--data' + sec)(function)
    return function


def df_filter_options2(function: Callable):
    return df_filter_options(function, second_df=True)


def get_filtered_df(filters: Dict[str, FILTER_DATATYPES], original_dataset: bool = False, second_df: bool = False) -> pd.DataFrame:
    # if year is set, it overrides min/max year
    # authors as last names, first names
    print("Filter documents")
    if second_df:
        sec = "2"
    else:
        sec = ""
    df = dataset_.get_dataset(original_dataset)

    venues = filters["venues" + sec]
    if venues is not None:
        venues_list = set(attributes_to_list(str(venues)))
        df = df[df["NS venue name"].isin(venues_list)]

    year = filters["year" + sec]
    if year is not None:
        df = df[df["AA year of publication"] == year]
    min_year = filters["min_year" + sec]
    if min_year is not None:
        df = df[df["AA year of publication"] >= min_year]
    max_year = filters["max_year" + sec]
    if max_year is not None:
        df = df[df["AA year of publication"] <= max_year]

    author = filters["author" + sec]
    if author is not None:
        df = df[df["AA authors list"].str.contains(author, case=False)]

    fauthor = filters["fauthor" + sec]
    if fauthor is not None:
        df = df[df["AA first author full name"].str.lower() == str(fauthor).lower()]

    data = filters["data" + sec]
    if data:
        selection = set(attributes_to_list(str(data)))
        if "all" not in selection:
            if "titles" not in selection:
                df["AA title"] = np.nan
            if "abstracts" not in selection:
                if "abstracts-rule" not in selection:
                    df[COLUMN_ABSTRACT] = df[COLUMN_ABSTRACT].mask(df[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE)
                if "abstracts-anth" not in selection:
                    df[COLUMN_ABSTRACT] = df[COLUMN_ABSTRACT].mask(df[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_ANTHOLOGY)

    return df


def attributes_to_list(attributes: str) -> List[str]:
    attributes_list = attributes.split(',')
    attributes_list = [venue.strip(" ") for venue in attributes_list]
    return attributes_list


def category_names(filters: Dict[str, FILTER_DATATYPES], second_df: bool = False) -> List[str]:
    category_name = []
    for key, value in filters.items():
        if value is not None and (("2" in key and second_df) or ("2" not in key and not second_df)):
            if not isinstance(value, bool):
                category_name.append(value)
            elif value:
                category_name.append(key)
    return category_name
