"""This module offers functions for count-based analysis."""
import os
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

import nlpland.data.clean as clean_
import nlpland.data.filter as filter_
from nlpland.constants import COLUMN_ABSTRACT, CURRENT_TIME, FILTER_DATATYPES


def generate_token_matrices(
    documents: List[List[str]], n_lower: int, n_upper: int
) -> Tuple[List[str], csr_matrix, TfidfTransformer]:
    """Generate a sparse term-document co-occurrence matrix and create a TfIdfTransformer that can
    be used to derive the idf scores and a matrix of tf-idf scores for term-document pairs from the
    first matrix.

    Occurrences can additionally also be counted for n-grams using the n_lower and n_upper
    parameters, e.g. n_lower=1 and n_upper=2 will results in all unigrams and bigrams being counted.

    Args:
        documents: The documents to count term occurrences in.
        n_lower: The lower bound for n-grams.
        n_upper: The upper bound for n-grams.

    Returns:
        List of all words.
        Sparse co-occurrence matrix of term-document pairs.
        TfIdfTransformer that can extract a tf-idf matrix or the idf vector.
    """
    english_words = clean_.english_words()
    stopwords = clean_.stopwords_and_more()
    lemmatizer = clean_.get_lemmatizer()
    vectorizer = CountVectorizer(
        analyzer="word",
        tokenizer=lambda doc: clean_.remove_stopwords(
            clean_.tokenize_and_lemmatize(doc, lemmatizer), stopwords
        ),
        preprocessor=lambda doc: clean_.newline_hyphens(doc, english_words),
        lowercase=True,
        ngram_range=(n_lower, n_upper),
    )
    # the sklearn tokenizer splits "open-source", nltk does not
    counts_matrix = vectorizer.fit_transform(documents)  # is a sparse matrix
    tfidf_matrix = TfidfTransformer(smooth_idf=True, use_idf=True).fit(counts_matrix)

    return vectorizer.get_feature_names(), counts_matrix, tfidf_matrix


def token_frequencies(df_papers: pd.DataFrame, ngrams: str) -> pd.DataFrame:
    """Calculate token frequencies and tf-idf scores and put them into one Dataframe.

    Args:
        df_papers: Dataframe with the papers to process.
        ngrams: The lower and upper bound of the n_grams, e.g. "1", "2", "1,2" or "1, 3".

    Returns:
        Dataframe with all terms and their tf and tf-idf scores.
    """
    ngrams_list = filter_.attributes_to_list(ngrams)
    if len(ngrams_list) > 1:
        n_upper = ngrams_list[1]
    else:
        n_upper = ngrams_list[0]

    documents = list(df_papers[COLUMN_ABSTRACT].dropna()) + list(df_papers["AA title"].dropna())
    feature_names, counts_matrix, tfidf_matrix = generate_token_matrices(
        documents, int(ngrams_list[0]), int(n_upper)
    )
    tf_score = np.asarray(counts_matrix.sum(axis=0))[0]
    idf_score = tfidf_matrix.idf_
    data = {"tf": tf_score, "tfidf": tf_score * idf_score}
    df_freq = pd.DataFrame(data=data, index=feature_names)
    return df_freq


def top_k_tokens(
    k: int, df_papers: pd.DataFrame, ngrams: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract the top k token from a dataframe both in regards to tf and tfidf score.

    Args:
        k: Determines how many tokens we show.
        df_papers: Dataframe with the papers to process.
        ngrams: The lower and upper bound of the n_grams, e.g. "1", "2", "1,2" or "1, 3".

    Returns:
        Dataframe with the top k entries by tf score.
        Dataframe with the top k entries by tf-idf score.
    """
    df_freq = token_frequencies(df_papers, ngrams)
    count_top = df_freq.sort_values(by=["tf"], ascending=False).head(k)
    tfidf_top = df_freq.sort_values(by=["tfidf"], ascending=False).head(k)
    return count_top, tfidf_top


def counts_over_time(  # pylint: disable=R0913, R0914
    df_papers: pd.DataFrame,
    k: int,
    ngrams: str,
    name: str,
    tfidf: bool,
    filters: Dict[str, FILTER_DATATYPES],
) -> None:
    """Plot the counts of all terms, that were in a top k in at least one year, over time. The time
    can be selected via the filters.

    Args:
        df_papers: Dataframe with the papers to process.
        k: Determines how many tokens are shown.
        ngrams: The lower and upper bound of the n_grams, e.g. "1", "2", "1,2" or "1, 3"
        name: Name of the output image.
        tfidf: If True, will rank by tf-idf not tf scores.
        filters: Dict of filters applied.
    """

    if tfidf:
        mode = "tfidf"
        filters["tfidf"] = True
    else:
        mode = "tf"

    years_freqs = {}
    tokens = set()
    years = sorted(df_papers["AA year of publication"].unique())
    for year in years:
        df_year = df_papers[df_papers["AA year of publication"] == year]
        count_top = token_frequencies(df_year, ngrams).sort_values(by=[mode], ascending=False)
        tokens.update(count_top.head(k).index)
        years_freqs[str(year)] = count_top
    df_years = pd.concat(years_freqs, axis=1)

    for token in tokens:
        plt.plot(years, df_years.loc[token, (slice(None), mode)], label=token)
    plt.xlabel("year")
    plt.ylabel(mode)
    plt.title(filter_.category_names(filters))
    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
    plt.ticklabel_format(useOffset=False)
    plt.xticks(years)
    plt.tight_layout()

    if name is None:
        name = f"ct_{CURRENT_TIME}"
    path = f"output/counts/{name}.png"
    plt.savefig(path)
    print(f"File created at {os.path.abspath(path)}")
