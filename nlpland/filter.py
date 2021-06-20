import click
import nlpland.dataset as data
import nlpland.data_cleanup as clean
from nlpland.constants import COLUMN_ABSTRACT

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


def get_filtered_df(venues: str, year: int, min_year: int, max_year: int, original_dataset: bool = False):
    # if year is set, it overrides min/max year
    df = data.get_dataset(original_dataset)
    df = df[~df[COLUMN_ABSTRACT].isna()]
    if venues is not None:
        venues_list = clean.venues_to_list(venues)
        df = df[df["NS venue name"].isin(venues_list)]
    if year is not None:
        df = df[df["AA year of publication"] == year]
    if min_year is not None:
        df = df[df["AA year of publication"] >= min_year]
    if max_year is not None:
        df = df[df["AA year of publication"] <= max_year]
    return df


def format_years(row, year, min_year, max_year, year2, min_year2, max_year2):
    if year is not None and row["AA year of publication"] == year:
        return f"{year}"
    if year2 is not None and row["AA year of publication"] == year2:
        return f"{year2}"
    if min_year is not None and max_year is not None and min_year <= row["AA year of publication"] <= max_year:
        return f"{min_year}-{max_year}"
    if min_year2 is not None and max_year2 is not None and min_year2 <= row["AA year of publication"] <= max_year2:
        return f"{min_year2}-{max_year2}"
    else:
        return ""


def edit_venues(row, venues, venues_list, venues2):
    if row["NS venue name"] in venues_list:
        val = venues
    else:
        val = venues2
    return val