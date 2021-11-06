"""This module provides the entry points for the CLI commands."""
import click
from click.testing import CliRunner
from dotenv import load_dotenv

import nlpland.data.check as check_
import nlpland.data.dataset as dataset_
import nlpland.data.filter as filter_
import nlpland.modules.count as count_
import nlpland.modules.scatter as scatter_
import nlpland.modules.semantic as semantic_
import nlpland.modules.topic_model as topic_
from nlpland.constants import (
    ABSTRACT_SOURCE_ANTHOLOGY,
    ABSTRACT_SOURCE_RULE,
    FILTER_DATATYPES,
)

load_dotenv()


@click.group()
def cli() -> None:
    """Executed before every command."""


@cli.command()
@filter_.df_filter_options
def download(**kwargs: FILTER_DATATYPES) -> None:
    """Download the papers that match the given filters.

    Args:
        **kwargs: Dict of filters to apply to the data before downloading.
    """
    df_filtered = filter_.get_filtered_df(kwargs)
    dataset_.download_papers(df_filtered)


@cli.command()
@click.argument("mode", type=str)
@click.option("--original", is_flag=True)
@click.option("--overwrite-rule", is_flag=True)  # only overwrites rule based abstracts
@filter_.df_filter_options
def extract(mode: str, original: bool, overwrite_rule: bool, **kwargs: FILTER_DATATYPES) -> None:
    """Extract abstracts with the specified method.

    Currently abstracts can be extracted from the ACL Anthology XML files and from the papers PDF
    files using a rule-based system.

    Args:
        mode: Determine the extraction method.
        original: If True, use the original, not expanded dataset.
        overwrite_rule: If True, overwrites abstracts previously extracted with this function.
        **kwargs: Dict of filters to apply to the data before the extraction.
    """
    df_full = dataset_.load_dataset(original)

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
    """Check the encoding for all extracted abstracts by searching for '�' in the abstracts."""
    df_papers = dataset_.load_dataset(False)
    check_.check_encoding_issues(df_papers)


@cli.command()
@click.option("--original", is_flag=True)
def checkdataset(original: bool) -> None:
    """Check the dataset and print various useful information about it.

    Args:
        original: If True, use the original, not expanded dataset.
    """
    df_papers = dataset_.load_dataset(original)
    check_.check_dataset(df_papers)


@cli.command()
@click.argument("paper-path", type=str)
def checkpaper(paper_path: str) -> None:
    """Parse a specific paper with tika and print its output.

    Args:
        paper_path: Filepath of the paper to check.
    """
    check_.check_paper_parsing(paper_path)


@cli.command()
def countabstractsanth() -> None:
    """Print the amount of abstracts in the ACL Anthology XML files."""
    check_.count_anthology_abstracts()


@cli.command()
@click.argument("k", type=int)
@click.option("--ngrams", type=str, default="1")
@filter_.df_filter_options
def count(k: int, ngrams: str, **kwargs: FILTER_DATATYPES) -> None:
    """Extract the top k token from a dataframe both in regards to tf and tfidf score.

    Args:
        k: Determines how many tokens we show.
        ngrams: The lower and upper bound of the n_grams, e.g. "1", "2", "1,2" or "1, 3".
        **kwargs: Dict of filter to apply to the data before analyzing the data.
    """
    # works like filters:
    # leaving both blank: whole dataset (once)
    # leaving the second blank: only count first one
    df_filtered = filter_.get_filtered_df(kwargs)

    count_top, tfidf_top = count_.top_k_tokens(k, df_filtered, ngrams)
    print(f"Most occurring words in selection:\n{count_top}")
    print(f"Highest tf-idf scores in selection:\n{tfidf_top}")


@cli.command()
@click.argument("k", type=int)
@click.option("-n", "--name", type=str)
@click.option("--ngrams", type=str, default="1")
@click.option("--tfidf", is_flag=True)
@filter_.df_filter_options
def counts_time(k: int, ngrams: str, name: str, tfidf: bool, **kwargs: FILTER_DATATYPES) -> None:
    """Plot the counts of all terms, that were in a top k in at least one year, over time. The time
    can be selected via the filters.

    Args:
        k: Determines how many tokens are shown.
        ngrams: The lower and upper bound of the n_grams, e.g. "1", "2", "1,2" or "1, 3"
        name: Name of the output image.
        tfidf: If True, will rank by tf-idf not tf scores.
        **kwargs: Dict of filter to apply to the data before analyzing the data.
    """
    df_filtered = filter_.get_filtered_df(kwargs)
    count_.counts_over_time(df_filtered, k, ngrams, name, tfidf, kwargs)  # pylint: disable=R0913


@cli.command()
@click.option("--fast", is_flag=True)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
@filter_.df_filter_options2
def scatter(fast: bool, name: str, **kwargs: FILTER_DATATYPES) -> None:
    """Plot the word counts using the package scattertext, by comparing two given sets of data.

    Highlight which words were more common in which set of data.

    Args:
        fast: If True, scattertext will be faster, but less accurate, by using a different model.
        name: Name of the output HTML file.
        **kwargs: Dict of filter to apply to the data before analyzing the data.
    """
    df_y = filter_.get_filtered_df(kwargs)
    df_x = filter_.get_filtered_df(kwargs, second_df=True)

    scatter_.plot_word_counts(df_y, df_x, fast, name, kwargs)


@cli.command()
@click.argument("topics", type=int)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
def topic_train(topics: int, name: str, **kwargs: FILTER_DATATYPES) -> None:
    """Train a topic model and create an interactive visualization using pyLDAvis.

    Args:
        topics: The amount of topics to train.
        name: The name of the model and output HTML file.
        **kwargs: Dict of filter to apply to the data before analyzing the data.
    """
    df_filtered = filter_.get_filtered_df(kwargs)
    topic_.topic(df_filtered, topics, name)


@cli.command()
@click.option("--train", is_flag=True)
@click.option("-n", "--name", type=str)
@filter_.df_filter_options
def fasttext(train: bool, name: str, **kwargs: FILTER_DATATYPES) -> None:
    """Train a semantic model using fastText with the given data, save it and evaluate it.

    Additionally evaluate the model with some tests.

    Args:
        train: If True, retrain the model with the given data.
        name: Name of the model.
        **kwargs: Dict of filter to apply to the data before analyzing the data.
    """
    df_filtered = filter_.get_filtered_df(kwargs)
    semantic_.semantic(df_filtered, train, name)


# @cli.command()
# @click.option("--train", is_flag=True)
# @filter_.df_filter_options
# def umap(**kwargs: FILTER_DATATYPES) -> None:
#     df_filtered = filter_.get_filtered_df(kwargs)
#     semantic_.plot(df)


@cli.command()
def test() -> None:
    """For testing purposes."""
    # from nlpland.data_cleanup import clean_and_tokenize
    # test_ = "one two, three.\n four-five, se-\nven, open-\nsource, se-\nve.n, "

    corpus = [
        "This is the first document.",
        "This document is the second document.",
        "And this is the third one.",
        "Is this the first document?",
        "one two, three.\n four-five, se-\nven, open-\nsource, se-\nve.n, ",
    ]
    print(corpus)
    # import nltk
    # print(nltk.stem.WordNetLemmatizer().lemmatize("models"))


if __name__ == "__main__":
    # this is for debugging via IDE

    runner = CliRunner()
    result = runner.invoke(count, args=["5"], catch_exceptions=False)
    # traceback.print_exception(*result.exc_info)
