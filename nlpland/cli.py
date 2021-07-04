import click
import pandas as pd
import numpy as np
import time
import os

import nlpland.dataset as data
import nlpland.data_check as check
import nlpland.wordcount as count_
from nlpland.constants import COLUMN_ABSTRACT
from dotenv import load_dotenv
import nlpland.filter as filter
import nlpland.topic_modelling as topic

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
@click.option('--ngrams', type=int, default=1)
@filter.df_filter_options
def count(k: int, ngrams: int, **kwargs):
    # TODO allow different sizes of ngrams
    # works like filters:
    # leaving both blank: whole dataset (once)
    # leaving the second blank: only count first one
    df1 = filter.get_filtered_df(kwargs)
    docs = list(df1[COLUMN_ABSTRACT]) + list(df1["AA title"])

    highest_count, highest_tfidf = count_.count_tokens(k, docs, ngrams)
    print(f"Most occuring words in selection: {highest_count}")
    print(f"Highest tf-idf scores in selection: {highest_tfidf}")


@cli.command()
@filter.df_filter_options
@filter.df_filter_options2
def scatter(**kwargs):
    np.seterr(divide='ignore', invalid='ignore')
    df1 = filter.get_filtered_df(kwargs)
    df2 = filter.get_filtered_df(kwargs, second_df=True)
    df = pd.concat([df1, df2])

    venues = kwargs["venues"]
    year = kwargs["year"]
    min_year = kwargs["min_year"]
    max_year = kwargs["max_year"]
    venues2 = kwargs["venues2"]
    year2 = kwargs["year2"]
    min_year2 = kwargs["min_year2"]
    max_year2 = kwargs["max_year2"]

    venues_list = filter.venues_to_list(venues)
    venues_list2 = filter.venues_to_list(venues2)

    if venues_list != venues_list2:
        df["category"] = df.apply(lambda x: filter.format_venues(x, venues_list), axis=1)
    elif year != year2 or min_year != min_year2 or max_year != max_year2:
        df["category"] = df.apply(lambda x: filter.format_years(x, year, min_year, max_year), axis=1)

    count_.plot_word_counts(df, kwargs)


@cli.command()
@click.argument('topics', type=int)
@filter.df_filter_options
def topic(topics: int, **kwargs):
    df = filter.get_filtered_df(kwargs)
    topic.topic(df, topics)


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

# TODO consistent import statements
