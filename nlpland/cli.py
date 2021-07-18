import click
import pandas as pd
import numpy as np
import time
import os

import nlpland.dataset as data
import nlpland.data_check as check
import nlpland.wordcount as count_
import nlpland.scatter as scatter_
from nlpland.constants import COLUMN_ABSTRACT, ABSTRACT_SOURCE_RULE, ABSTRACT_SOURCE_ANTHOLOGY
from dotenv import load_dotenv
import nlpland.filter as filter
import nlpland.topic_modelling as topic_
import nlpland.semantic as semantic

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
@click.option('--overwrite', is_flag=True)  # always only overwrites rule based abstracts
@click.option('--min-year', type=int)
@click.option('--max-year', type=int)
def extract(mode, original, overwrite, min_year, max_year):
    df = data.get_dataset(original)

    modes = [ABSTRACT_SOURCE_RULE, ABSTRACT_SOURCE_ANTHOLOGY]
    if mode not in modes:
        print(f"Unsupported mode '{mode}'. Choose from {modes}.")
    if mode == ABSTRACT_SOURCE_RULE:
        data.extract_abstracts_rulebased(df, overwrite=overwrite, min_year=min_year, max_year=max_year)
    elif mode == ABSTRACT_SOURCE_ANTHOLOGY:
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
    df = filter.get_filtered_df(kwargs)

    highest_count, highest_tfidf = count_.count_tokens(k, df, ngrams)
    print(f"Most occurring words in selection: {highest_count}")
    print(f"Highest tf-idf scores in selection: {highest_tfidf}")


@cli.command()
@filter.df_filter_options
@filter.df_filter_options2
def scatter(**kwargs):
    # np.seterr(divide='ignore', invalid='ignore')
    df1 = filter.get_filtered_df(kwargs)
    df2 = filter.get_filtered_df(kwargs, second_df=True)

    scatter_.plot_word_counts(df1, df2, kwargs)


@cli.command()
@click.argument('topics', type=int)
@filter.df_filter_options
def topic(topics: int, **kwargs):
    df = filter.get_filtered_df(kwargs)
    topic_.topic(df, topics)


@cli.command()
@click.option('--train', is_flag=True)
@filter.df_filter_options
def fasttext(train: bool, **kwargs):
    df = filter.get_filtered_df(kwargs)
    semantic.semantic(df, train)


@cli.command()
@click.option('--train', is_flag=True)
@filter.df_filter_options
def umap(**kwargs):
    df = filter.get_filtered_df(kwargs)
    semantic.plot(df)


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

    df = data.get_dataset(original_dataset=False)
    # df = df[~df[COLUMN_ABSTRACT].isna()]
    df["1"] = df["AA authors list"].str.lower()
    print(df["1"].str.contains("jurafsky, dan").sum())
    print(df["1"].str.contains("manning, christopher").sum())
    print(df["1"].str.contains("manning, christopher|jurafsky, dan").sum())
    print(len(df[(df["1"].str.contains("manning, christopher")) & (df["1"].str.contains("jurafsky, dan"))]))
    # print(df["1"].str.contains("Card, Dallas && Gabriel, Saadia").sum())


if __name__ == '__main__':
    # debugging
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(count, args=["5"], catch_exceptions=False)
    # traceback.print_exception(*result.exc_info)
