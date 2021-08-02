import click

import nlpland.data.dataset as dataset_
import nlpland.data.check as check_
import nlpland.modules.count as count_
import nlpland.modules.scatter as scatter_
from nlpland.constants import ABSTRACT_SOURCE_RULE, ABSTRACT_SOURCE_ANTHOLOGY
from dotenv import load_dotenv
import nlpland.data.filter as filter_
import nlpland.modules.topic_model as topic_
import nlpland.modules.semantic as semantic_

load_dotenv()


@click.group()
def cli() -> None:
    pass


#TODO switch to different filter
@cli.command()
@click.option('--min-year', type=int)
@click.option('--max-year', type=int)
def download(min_year, max_year):
    df = dataset_.get_dataset(True)
    dataset_.download_papers(df, min_year=min_year, max_year=max_year)


#TODO switch to different filter
@cli.command()
@click.argument('mode', type=str)
@click.option('--original', is_flag=True)
@click.option('--overwrite-rule', is_flag=True)  # always only overwrites rule based abstracts
@click.option('--min-year', type=int)
@click.option('--max-year', type=int)
def extract(mode, original, overwrite_rule, min_year, max_year):
    df = dataset_.get_dataset(original)

    modes = [ABSTRACT_SOURCE_RULE, ABSTRACT_SOURCE_ANTHOLOGY]
    if mode not in modes:
        print(f"Unsupported mode '{mode}'. Choose from {modes}.")
    if mode == ABSTRACT_SOURCE_RULE:
        dataset_.extract_abstracts_rulebased(df, overwrite_rule=overwrite_rule, min_year=min_year, max_year=max_year)
    elif mode == ABSTRACT_SOURCE_ANTHOLOGY:
        dataset_.extract_abstracts_anthology(df)


@cli.command()
def checkencode():
    df = dataset_.get_dataset(False)
    check_.check_encoding_issues(df)


@cli.command()
@click.option('--original', is_flag=True)
def checkdataset(original):
    df = dataset_.get_dataset(original)
    check_.check_dataset(df)


@cli.command()
@click.argument('paper-path', type=str)
def checkpaper(paper_path):
    check_.check_paper_parsing(paper_path)


@cli.command()
def countabstractsanth():
    check_.count_anthology_abstracts()


@cli.command()
@click.argument('k', type=int)
@click.option('--ngrams', type=str, default="1")
@filter_.df_filter_options
def count(k: int, ngrams: str, **kwargs):
    # works like filters:
    # leaving both blank: whole dataset (once)
    # leaving the second blank: only count first one
    df = filter_.get_filtered_df(kwargs)

    count_top, tfidf_top = count_.top_k_tokens(k, df, ngrams)
    print(f"Most occurring words in selection:\n{count_top}")
    print(f"Highest tf-idf scores in selection:\n{tfidf_top}")


@cli.command()
@click.argument('k', type=int)
@click.option("-n", "--name", type=str)
@click.option('--ngrams', type=str, default="1")
@click.option('--tfidf', is_flag=True)
@filter_.df_filter_options
def counts_time(k: int, ngrams: str, name: str, tfidf: bool, **kwargs):
    df = filter_.get_filtered_df(kwargs)
    count_.counts_over_time(df, k, ngrams, name, tfidf, kwargs)


@cli.command()
@click.option("--fast", is_flag=True)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
@filter_.df_filter_options2
def scatter(fast, name: str, **kwargs):
    df1 = filter_.get_filtered_df(kwargs)
    df2 = filter_.get_filtered_df(kwargs, second_df=True)

    scatter_.plot_word_counts(df1, df2, fast, name, kwargs)


@cli.command()
@click.argument('topics', type=int)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
def topic_train(topics: int, name: str, **kwargs):
    df = filter_.get_filtered_df(kwargs)
    topic_.topic(df, topics, name)


@cli.command()
@click.option('--train', is_flag=True)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
def fasttext(train: bool, name: str, **kwargs):
    df = filter_.get_filtered_df(kwargs)
    semantic_.semantic(df, train, name)


@cli.command()
@click.option('--train', is_flag=True)
@filter_.df_filter_options
def umap(**kwargs):
    df = filter_.get_filtered_df(kwargs)
    semantic_.plot(df)


@cli.command()
def load():
    pass


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
    import nltk
    print(nltk.stem.WordNetLemmatizer().lemmatize("models"))

    quit()

    df = dataset_.get_dataset(original_dataset=False)
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
