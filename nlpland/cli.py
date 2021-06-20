import click
import pandas as pd

import nlpland.dataset as data
import nlpland.data_check as check
import nlpland.wordcount as count_
from nlpland.constants import COLUMN_ABSTRACT
from dotenv import load_dotenv
from nlpland import filter

load_dotenv()


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--min-year', type=int)
@click.option('--max-year', type=int)
def download(min_year, max_year):
    df = data.get_dataset(True)
    data.download_papers(df, min_year=min_year, max_year=max_year)


@cli.command()
@click.argument('mode', type=str)
@click.option('--original', is_flag=True)
@click.option('--overwrite', is_flag=True)
@click.option('--min-year', type=int)
@click.option('--max-year', type=int)
def extract(mode, original, overwrite, min_year, max_year):
    df = data.get_dataset(original)

    modes = ["rule", "anth"]
    if mode not in modes:
        print(f"Unsupported mode '{mode}'. Choose from {modes}.")
    if mode == "rule":
        data.extract_abstracts_rulebased(df, overwrite_abstracts=overwrite, min_year=min_year, max_year=max_year)
    elif mode == "anth":
        data.extract_abstracts_anthology(df)


@cli.command()
def checkencode():
    df = data.get_dataset(False)
    check.check_encoding_issues(df)


@cli.command()
@click.option('--original', is_flag=True)
def checkdataset(original):
    df = data.get_dataset(original)
    check.check_dataset(df)


@cli.command()
@click.argument('paper-path', type=str)
def checkpaper(paper_path):
    check.check_paper_parsing(paper_path)


@cli.command()
def countabstractsanth():
    check.count_anthology_abstracts()


@cli.command()
def grobid():
    from grobid_client.grobid_client import GrobidClient
    import time
    import os
    start = time.time()
    client = GrobidClient(config_path="C:/Users/Lennart/Desktop/grobid_client_python/config.json")
    path = "C:/test_papers"
    if os.path.isdir(path):
        print(f"Processing {len(os.listdir(path))} files.")
    client.process("processFulltextDocument", path, output="./resources/test_out_heavy/", n=20)
    print(f"This took {time.time()-start}s.")
    # TODO cleanup


@cli.command()
@click.argument('k', type=int)
@click.option('--ngrams', type=int)
@filter.df_filter_options
@filter.df_filter_options2
def count(k: int, venues: str, year: int, min_year: int, max_year: int, venues2: str, year2: int, min_year2: int, max_year2: int, ngrams: int = 1):
    # works like filters:
    # leaving both blank: whole dataset (once)
    # leaving the second blank: only count first one
    df1 = filter.get_filtered_df(venues, year, min_year, max_year)
    docs = list(df1[COLUMN_ABSTRACT]) + list(df1["AA title"])

    if venues2 is not None or year2 is not None or min_year2 is not None or max_year2 is not None:
        df2 = filter.get_filtered_df(venues2, year2, min_year2, max_year2)
        docs2 = list(df2[COLUMN_ABSTRACT]) + list(df2["AA title"])
        count_.count_and_compare(10, docs, docs2, n=ngrams)
        count_.count_and_compare_words(k, df1, df2, n=ngrams)
    else:
        count_.count_and_compare(10, docs, n=ngrams)
        count_.count_and_compare_words(k, df1, n=ngrams)


@cli.command()
@filter.df_filter_options
@filter.df_filter_options2
def scatter(venues: str, year: int, min_year: int, max_year: int, venues2: str, year2: int, min_year2: int, max_year2: int):
    import numpy as np
    np.seterr(divide='ignore', invalid='ignore')

    df1 = filter.get_filtered_df(venues, year, min_year, max_year)
    df2 = filter.get_filtered_df(venues2, year2, min_year2, max_year2)
    df = pd.concat([df1, df2])

    venues_list = filter.venues_to_list(venues)
    venues_list2 = filter.venues_to_list(venues2)
    df["NS venue name"] = df.apply(lambda x: filter.edit_venues(x, venues, venues_list, venues2), axis=1)

    if venues_list == venues_list2:
        if year is not None:
            years = f"{year}"
        else:
            years = f"{min_year}-{max_year}"
        if year2 is not None:
            years2 = f"{year2}"
        else:
            years2 = f"{min_year2}-{max_year2}"
        df["year"] = df.apply(lambda x: filter.format_years(x, year, min_year, max_year, year2, min_year2, max_year2), axis=1)
        count_.plot_word_counts(df, venues, venues2, years, years2)
    else:
        count_.plot_word_counts(df, venues, venues2)


@cli.command()
@click.argument('topics', type=int)
@click.option('--load', is_flag=True)
@filter.df_filter_options
# @filter.df_filter_options2
def topic(topics: int, venues: str, year: int, min_year: int, max_year: int, load=False):
    from nlpland.topic_modelling import topic
    df = filter.get_filtered_df(venues, year, min_year, max_year)
    topic(df, topics, load)


@cli.command()
def test():
    # from nlpland.data_cleanup import clean_and_tokenize
    # test_ = "one two, three.\n four-five, se-\nven, open-\nsource, se-\nve.n, "

    corpus = [
        'This is the first document.',
        'This document is the second document.',
        'And this is the third one.',
        'Is this the first document?',
        "one two, three.\n four-five, se-\nven, open-\nsource, se-\nve.n, ",
    ]


if __name__ == '__main__':
    # debugging
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(extract, ["anth", "--original"])
    # traceback.print_exception(*result.exc_info)
