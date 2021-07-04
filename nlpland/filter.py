import click
import nlpland.dataset as data
from nlpland.constants import COLUMN_ABSTRACT
from typing import Dict, Any

#
# def filter_options(function):

#     return function


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
    function = click.option('--institution' + sec)(function)
    function = click.option('--location' + sec)(function)
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

    author = filters["author" + sec]
    if author is not None:
        df = df[df["AA authors list"].str.contains(author, case=False)]
    # TODO maybe add location/institution (not in dataset)
    return df


def venues_to_list(venues: str):
    if venues is not None:
        venues_list = venues.split(',')
        venues_list = [venue.strip(" ") for venue in venues_list]
        return venues_list
    else:
        return None


def category_years(row, year, min_year, max_year):
    if (year is not None and row["AA year of publication"] == year) or\
            (min_year is not None and max_year is not None and min_year <= row["AA year of publication"] <= max_year):
        return "c1"
    else:
        return "c2"


def category_venues(row, venues_list):
    if row["NS venue name"] in venues_list:
        return "c1"
    else:
        return "c2"


def category_authors(row, author):
    if author in row["AA authors list"].lower():
        return "c1"
    else:
        return "c2"



def category_names(filters, second_df: bool = False):
    category_name = []
    for key, value in filters.items():
        if value is not None and (("2" in key and second_df) or ("2" not in key and not second_df)):
            category_name.append(value)
    return category_name
