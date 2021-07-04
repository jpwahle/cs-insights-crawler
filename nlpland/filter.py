import click
import nlpland.dataset as data
import nlpland.clean as clean
from nlpland.constants import COLUMN_ABSTRACT
from typing import Dict, Any


def df_filter_options(function):
    function = click.option('--venues')(function)
    function = click.option('--year', type=int)(function)
    function = click.option('--min-year', type=int)(function)
    function = click.option('--max-year', type=int)(function)
    return function


def df_filter_options2(function):
    function = click.option('--venues2')(function)
    function = click.option('--year2', type=int)(function)
    function = click.option('--min-year2', type=int)(function)
    function = click.option('--max-year2', type=int)(function)
    return function


# def is_valid_key(key, kwargs):
#     return key in kwargs.keys() and kwargs[key] is not None


def get_filtered_df(filters: Dict[str, Any], original_dataset: bool = False, second_df: bool = False):
    # if year is set, it overrides min/max year
    if second_df:
        sec = "2"
    else:
        sec = ""
    df = data.get_dataset(original_dataset)
    df = df[~df[COLUMN_ABSTRACT].isna()]
    venues = filters["venues" + sec]
    if venues is not None:
        venues_list = venues_to_list(venues)
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
    return df


def venues_to_list(venues: str):
    venues_list = venues.split(',')
    venues_list = [venue.strip(" ") for venue in venues_list]
    return venues_list


def format_years(row, year, min_year, max_year):
    if (year is not None and row["AA year of publication"] == year) or\
            (min_year is not None and max_year is not None and min_year <= row["AA year of publication"] <= max_year):
        return "c1"
    else:
        return "c2"


def format_venues(row, venues_list):
    if row["NS venue name"] in venues_list:
        return "c1"
    else:
        return "c2"


def category_names(filters, second_df: bool = False):
    category_name = []
    for key, value in filters.items():
        if value is not None and (("2" in key and second_df) or ("2" not in key and not second_df)):
            category_name.append(value)
    return category_name
