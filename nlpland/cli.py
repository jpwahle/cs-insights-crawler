import click
from dotenv import load_dotenv

import nlpland.data.check as check_
import nlpland.data.dataset as dataset_
import nlpland.data.filter as filter_
import nlpland.modules.count as count_
import nlpland.modules.scatter as scatter_
import nlpland.modules.semantic as semantic_
import nlpland.modules.topic_model as topic_
from nlpland.constants import (ABSTRACT_SOURCE_ANTHOLOGY, ABSTRACT_SOURCE_RULE,
                               FILTER_DATATYPES)

load_dotenv()


@click.group()
def cli() -> None:
    pass


@cli.command()
@filter_.df_filter_options
def download(**kwargs: FILTER_DATATYPES) -> None:
    df = filter_.get_filtered_df(kwargs)
    dataset_.download_papers(df)


@cli.command()
@click.argument('mode', type=str)
@click.option('--original', is_flag=True)
@click.option('--overwrite-rule', is_flag=True)  # only overwrites rule based abstracts
@filter_.df_filter_options
def extract(mode: str, original: bool, overwrite_rule: bool, **kwargs: FILTER_DATATYPES) -> None:
    df_full = dataset_.get_dataset(original)

    modes = [ABSTRACT_SOURCE_RULE, ABSTRACT_SOURCE_ANTHOLOGY]
    if mode not in modes:
        print(f"Unsupported mode '{mode}'. Choose from {modes}.")
    if mode == ABSTRACT_SOURCE_RULE:
        df_select = filter_.get_filtered_df(kwargs, original_dataset=original)
        dataset_.extract_abstracts_rulebased(df_select, df_full, overwrite_rule=overwrite_rule)
    elif mode == ABSTRACT_SOURCE_ANTHOLOGY:
        dataset_.extract_abstracts_anthology(df_full)


@cli.command()
def checkencode() -> None:
    df = dataset_.get_dataset(False)
    check_.check_encoding_issues(df)


@cli.command()
@click.option('--original', is_flag=True)
def checkdataset(original: bool) -> None:
    df = dataset_.get_dataset(original)
    check_.check_dataset(df)


@cli.command()
@click.argument('paper-path', type=str)
def checkpaper(paper_path: str) -> None:
    check_.check_paper_parsing(paper_path)


@cli.command()
def countabstractsanth() -> None:
    check_.count_anthology_abstracts()


@cli.command()
@click.argument('k', type=int)
@click.option('--ngrams', type=str, default="1")
@filter_.df_filter_options
def count(k: int, ngrams: str, **kwargs: FILTER_DATATYPES) -> None:
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
def counts_time(k: int, ngrams: str, name: str, tfidf: bool, **kwargs: FILTER_DATATYPES) -> None:
    df = filter_.get_filtered_df(kwargs)
    count_.counts_over_time(df, k, ngrams, name, tfidf, kwargs)


@cli.command()
@click.option("--fast", is_flag=True)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
@filter_.df_filter_options2
def scatter(fast: bool, name: str, **kwargs: FILTER_DATATYPES) -> None:
    df1 = filter_.get_filtered_df(kwargs)
    df2 = filter_.get_filtered_df(kwargs, second_df=True)

    scatter_.plot_word_counts(df1, df2, fast, name, kwargs)


@cli.command()
@click.argument('topics', type=int)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
def topic_train(topics: int, name: str, **kwargs: FILTER_DATATYPES) -> None:
    df = filter_.get_filtered_df(kwargs)
    topic_.topic(df, topics, name)


@cli.command()
@click.option('--train', is_flag=True)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
def fasttext(train: bool, name: str, **kwargs: FILTER_DATATYPES) -> None:
    df = filter_.get_filtered_df(kwargs)
    semantic_.semantic(df, train, name)


@cli.command()
@click.option('--train', is_flag=True)
@filter_.df_filter_options
def umap(**kwargs: FILTER_DATATYPES) -> None:
    df = filter_.get_filtered_df(kwargs)
    semantic_.plot(df)


@cli.command()
def test() -> None:
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


if __name__ == '__main__':
    # this is for debugging via IDE
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(count, args=["5"], catch_exceptions=False)
    # traceback.print_exception(*result.exc_info)
