import click
import numpy as np

import nlpland.data.dataset as dataset_
from nlpland.constants import COLUMN_ABSTRACT, COLUMN_ABSTRACT_SOURCE, ABSTRACT_SOURCE_RULE, ABSTRACT_SOURCE_ANTHOLOGY
from typing import Dict, Any, List


def df_filter_options(function, second_df: bool = False):
    if second_df:
        sec = "2"
    else:
        sec = ""
    function = click.option('--venues' + sec)(function)
    function = click.option('--year' + sec, type=int)(function)
    function = click.option('--min-year' + sec, type=int)(function)
    function = click.option('--max-year' + sec, type=int)(function)
    function = click.option('--author' + sec)(function)
    function = click.option('--data' + sec)(function)
    return function


def df_filter_options2(function):
    return df_filter_options(function, second_df=True)


def get_filtered_df(filters: Dict[str, Any], original_dataset: bool = False, second_df: bool = False):
    # if year is set, it overrides min/max year
    # authors as last names, first names
    if second_df:
        sec = "2"
    else:
        sec = ""
    df = dataset_.get_dataset(original_dataset)

    venues = filters["venues" + sec]
    if venues is not None:
        venues_list = set(attributes_to_list(venues))
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

    data = filters["data" + sec]
    if data:
        selection = set(attributes_to_list(data))
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


def category_names(filters, second_df: bool = False):
    category_name = []
    for key, value in filters.items():
        if value is not None and (("2" in key and second_df) or ("2" not in key and not second_df)):
            if type(value) != bool:
                category_name.append(value)
            elif value:
                category_name.append(key)
    return category_name
