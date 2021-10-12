"""This module offers functions for the count-based analysis using the package scattertext."""
import os
from typing import Dict

import pandas as pd
import scattertext as st
import spacy

import nlpland.data.clean as clean_
import nlpland.data.filter as filter_
from nlpland.constants import COLUMN_ABSTRACT, CURRENT_TIME, FILTER_DATATYPES

CATEGORY = "category"
PARSE = "parse"


def preprocess_dfs(df_y: pd.DataFrame, df_x: pd.DataFrame, fast: bool) -> pd.DataFrame:
    """Preprocess the two given dataframes, so scattertext can distinguish the two classes it is
    supposed to visualize, and combine them into one dataframe.

    Args:
        df_y: Dataframe that holds the data that will go on the y-axis.
        df_x: Dataframe that holds the data that will go on the x-axis.
        fast: If True, scattertext will be faster, but less accurate, by using a different model.

    Returns:
        Preprocessed and combined dataframe.
    """
    df_y[CATEGORY] = "c1"
    df_x[CATEGORY] = "c2"
    df_full = pd.concat([df_y, df_x])

    english_words = clean_.english_words()

    df_titles = df_full[[CATEGORY, "AA title"]]
    df_titles = df_titles.dropna(subset=["AA title"])
    df_titles = df_titles.rename(columns={"AA title": PARSE})
    df_abstracts = df_full[[CATEGORY, COLUMN_ABSTRACT]]
    df_abstracts = df_abstracts.dropna(subset=[COLUMN_ABSTRACT])
    df_abstracts[COLUMN_ABSTRACT] = df_abstracts[COLUMN_ABSTRACT].apply(
        lambda x: clean_.newline_hyphens(x, english_words)
    )
    df_abstracts = df_abstracts.rename(columns={COLUMN_ABSTRACT: PARSE})
    df_full = pd.concat([df_titles, df_abstracts])

    # df_full[PARSE] = df_full[COLUMN_ABSTRACT].apply(st.whitespace_nlp)
    # the above one is even faster, but breaks if lemmatization is active
    if fast:
        model = "en_core_web_sm"
    else:
        model = "en_core_web_trf"
    nlp = spacy.load(name=model, disable=["ner", "textcat", "custom"])
    df_full[PARSE] = df_full[PARSE].apply(nlp)

    return df_full


def plot_word_counts(
    df_y: pd.DataFrame,
    df_x: pd.DataFrame,
    fast: bool,
    name: str,
    filters: Dict[str, FILTER_DATATYPES],
) -> None:
    """Plot the word counts using the package scattertext, by comparing two given sets of data.

    Highlight which words were more common in which set of data.

    Args:
        df_y: Dataframe that holds the data that will go on the y-axis.
        df_x: Dataframe that holds the data that will go on the x-axis.
        fast: If True, scattertext will be faster, but less accurate, by using a different model.
        name: Name of the output HTML file.
        filters: Filters that were applied to the subsets.
    """
    df_full = preprocess_dfs(df_y, df_x, fast)
    stopwords = clean_.stopwords_and_more()

    corpus = (
        st.CorpusFromParsedDocuments(
            df_full,
            category_col=CATEGORY,
            parsed_col=PARSE,
            feats_from_spacy_doc=st.FeatsFromSpacyDoc(use_lemmas=True),
        )
        .build()
        .remove_terms(list(stopwords), ignore_absences=True)
        .get_unigram_corpus()
        .compact(st.AssociationCompactor(2000))
    )

    html = st.produce_scattertext_explorer(
        corpus,
        category="c1",
        category_name=str(filter_.category_names(filters)),
        not_category_name=str(filter_.category_names(filters, second_df=True)),
        minimum_term_frequency=5,
        pmi_threshold_coefficient=0,
        width_in_pixels=1000,
        transform=st.Scalers.dense_rank,
    )
    if name is None:
        name = f"st_{CURRENT_TIME}"
    path = f"output/scattertext/{name}.html"
    with open(path, "w+", encoding="UTF-8") as file:
        file.write(html)
        print(f"File created at {os.path.abspath(path)}")
