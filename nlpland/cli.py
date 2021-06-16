import click
import pandas as pd

import nlpland.dataset as data
import nlpland.data_cleanup as clean
import nlpland.data_check as check
import nlpland.wordcount as count_
from nlpland.constants import COLUMN_ABSTRACT
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--min-year')
@click.option('--max-year')
def download(min_year, max_year):
    df = data.get_dataset(True)
    data.download_papers(df, min_year=min_year, max_year=max_year)


@cli.command()
@click.argument('mode', type=str)
@click.option('--original', is_flag=True)
@click.option('--overwrite', is_flag=True)
@click.option('--min-year')
@click.option('--max-year')
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


# TODO move to helper
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
    if venues is not None:
        venues_list = clean.venues_to_list(venues)
        df = df[df["NS venue name"].isin(venues_list)]
    if year is not None:
        df = df[df["AA year of publication"] == year]
    if min_year is not None:
        df = df[df["AA year of publication"] >= year]
    if max_year is not None:
        df = df[df["AA year of publication"] <= year]
    return df


@cli.command()
@click.argument('k', type=int)
@click.option('--bigrams', is_flag=True)
@df_filter_options
@df_filter_options2
def count(k: int, venues: str, year: int, min_year: int, max_year: int, venues2: str, year2: int, min_year2: int, max_year2: int, bigrams: bool= False):
    # works like filters:
    # leaving both blank: whole dataset (once)
    # leaving the second blank: only count first one
    df1 = get_filtered_df(venues, year, min_year, max_year)
    docs = list(df1[COLUMN_ABSTRACT])+list(df1["AA title"])
    # TODO change to use n as input from the user
    if not bigrams:
        count_.count_and_compare(10, docs)
    else:
        count_.count_and_compare(10, docs, n=2)

    if venues2 is not None or year2 is not None or min_year2 is not None or max_year2 is not None:
        df2 = get_filtered_df(venues2, year2, min_year2, max_year2)
        if bigrams:
            count_.count_and_compare_bigrams(k, df1, df2)
        else:
            count_.count_and_compare_words(k, df1, df2)
    else:
        if bigrams:
            count_.count_and_compare_bigrams(k, df1)
        else:
            count_.count_and_compare_words(k, df1)


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
    # clean_and_tokenize(test_, get_vocabulary())
    count_.count_and_compare(10, corpus)

    # print(X.toarray())
    #
    # vectorizer2 = CountVectorizer(analyzer='word', ngram_range=(2, 2))
    # X2 = vectorizer2.fit_transform(corpus)
    # print(vectorizer2.get_feature_names())


if __name__ == '__main__':
    # debugging
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(extract, ["anth", "--original"])
    # traceback.print_exception(*result.exc_info)
