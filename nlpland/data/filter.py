"""This module offer functions to filter and transform the data."""
from typing import Callable, Dict, List

import click
import numpy as np
import pandas as pd

import nlpland.data.dataset as dataset_
from nlpland.constants import (
    ABSTRACT_SOURCE_ANTHOLOGY,
    ABSTRACT_SOURCE_RULE,
    COLUMN_ABSTRACT,
    COLUMN_ABSTRACT_SOURCE,
    FILTER_DATATYPES,
)


def df_filter_options(function: Callable, second_df: bool = False):
    """Combine multiple CLI filter options in one annotation.

    The use of second_df enables the use of a second set of the same filters.

    Args:
        function: Function which we extend.
        second_df: If True, add "2" to the name of options.

    Returns:
        Expanded function for the annotation.
    """
    if second_df:
        sec = "2"
    else:
        sec = ""
    function = click.option("--venues" + sec)(function)
    function = click.option("--year" + sec, type=int)(function)
    function = click.option("--min-year" + sec, type=int)(function)
    function = click.option("--max-year" + sec, type=int)(function)
    function = click.option("--author" + sec)(function)
    function = click.option("--fauthor" + sec)(function)
    function = click.option("--data" + sec)(function)
    return function


def df_filter_options2(function: Callable):
    """Provide an annotation for a second set of the same CLI filter options.

    Args:
        function: Function we expand.

    Returns:
        Expanded function.
    """
    return df_filter_options(function, second_df=True)


def mask_data(df_filtered: pd.DataFrame,
              data_filter: str,
              ) -> pd.DataFrame:
    """Mask the data (tiles/abstracts) in given dataframe based on given conditions.

    Args:
        df_filtered: Dataframe with the data to mask.
        data_filter: Filter for the data.

    Returns:
        Dataframe with (partially) masked data.
    """
    selection = set(attributes_to_list(str(data_filter)))
    print("selection:", selection)
    if "all" not in selection:
        if "titles" not in selection:
            df_filtered["AA title"] = np.nan
        if "abstracts" not in selection:
            if "abstracts-rule" not in selection:
                df_filtered[COLUMN_ABSTRACT] = df_filtered[COLUMN_ABSTRACT].mask(
                    df_filtered[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE
                )
            if "abstracts-anth" not in selection:
                df_filtered[COLUMN_ABSTRACT] = df_filtered[COLUMN_ABSTRACT].mask(
                    df_filtered[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_ANTHOLOGY
                )
    return df_filtered


def get_filtered_df(
    filters: Dict[str, FILTER_DATATYPES],
    original_dataset: bool = False,
    second_df: bool = False,
) -> pd.DataFrame:
    """Filter a dataframe with papers based on a given Dict of filters.

    Ignore the second set of filters, which options end with "2", unless specified.

    Args:
        filters: Dictionary of filters to apply.
        original_dataset: If True, load the original, not the expanded, dataset.
        second_df: If True, only use the options which names end with "2" to filter.

    Returns:
        Filtered and masked dataframe.
    """
    # if year is set, it overrides min/max year
    # authors as last names, first names
    print("Filter documents")
    if second_df:
        sec = "2"
    else:
        sec = ""
    df_filtered = dataset_.load_dataset(original_dataset)

    venues = filters["venues" + sec]
    if venues is not None:
        venues_list = set(attributes_to_list(str(venues)))
        df_filtered = df_filtered[df_filtered["NS venue name"].isin(venues_list)]

    year = filters["year" + sec]
    if year is not None:
        df_filtered = df_filtered[df_filtered["AA year of publication"] == year]
    min_year = filters["min_year" + sec]
    if min_year is not None:
        df_filtered = df_filtered[df_filtered["AA year of publication"] >= min_year]
    max_year = filters["max_year" + sec]
    if max_year is not None:
        df_filtered = df_filtered[df_filtered["AA year of publication"] <= max_year]

    author = filters["author" + sec]
    if author is not None:
        df_filtered = df_filtered[
            df_filtered["AA authors list"].str.contains(author, case=False)
        ]

    fauthor = filters["fauthor" + sec]
    if fauthor is not None:
        df_filtered = df_filtered[
            df_filtered["AA first author full name"].str.lower() == str(fauthor).lower()
        ]

    data_filter = filters["data" + sec]
    if data_filter:
        df_filtered = mask_data(df_filtered, str(data_filter))

    return df_filtered


def attributes_to_list(attributes: str) -> List[str]:
    """Transform a string with potentially multiple attributes to a list of the attributes.

    Args:
        attributes: Attributes as a single string.

    Returns:
        List of attributes.
    """
    attributes_list = attributes.split(",")
    attributes_list = [venue.strip(" ") for venue in attributes_list]
    return attributes_list


def category_names(
    filters: Dict[str, FILTER_DATATYPES], second_df: bool = False
) -> List[str]:
    """Turn the dict of filters into a list of attributes of the set filters to name a category.

    Ignore the second set of filters, which options end with "2", unless specified.

    Args:
        filters: Dict of filters to convert.
        second_df: If True, only use the options which names end with "2" to filter.

    Returns:
        List of set filter attributes.
    """
    category_name = []
    for key, value in filters.items():
        if value is not None and (
            ("2" in key and second_df) or ("2" not in key and not second_df)
        ):
            if not isinstance(value, bool):
                category_name.append(value)
            elif value:
                category_name.append(key)
    return category_name
