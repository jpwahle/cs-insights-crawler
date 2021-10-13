"""This module provides functions to train and evaluate a topic model based on the given data."""
import os

import gensim
import pandas as pd
import pyLDAvis
import pyLDAvis.gensim_models

import nlpland.data.clean as clean_
from nlpland.constants import COLUMN_ABSTRACT, CURRENT_TIME


def topic(df_papers: pd.DataFrame, topics: int, name: str) -> None:  # pylint: disable=R0914
    """Train a topic model and create an interactive visualization using pyLDAvis.

    Args:
        df_papers: Dataframe with the papers to build the model from.
        topics: The amount of topics to train.
        name: The name of the model and output HTML file.

    Returns:

    """
    print("Preprocess docs")
    english_words = clean_.english_words()
    stopwords = clean_.stopwords_and_more()
    lemmatizer = clean_.get_lemmatizer()
    abstracts = df_papers[COLUMN_ABSTRACT].dropna()
    titles = df_papers["AA title"].dropna()
    cleaned_abstracts = list(
        abstracts.apply(
            lambda text: clean_.preprocess_text(text, english_words, lemmatizer, stopwords)
        )
    )
    cleaned_titles = list(
        titles.apply(
            lambda text: clean_.preprocess_text(text, english_words, lemmatizer, stopwords)
        )
    )
    cleaned_docs = cleaned_titles + cleaned_abstracts

    print("Create model")
    dictionary = gensim.corpora.Dictionary(cleaned_docs)
    bow_corpus = [dictionary.doc2bow(doc) for doc in cleaned_docs]

    lda_model = gensim.models.LdaMulticore(
        bow_corpus, num_topics=topics, id2word=dictionary, passes=10, workers=2
    )
    print("Save model and results")
    if name is None:
        name_model = f"lda_{topics}_{CURRENT_TIME}"
        name_vis = f"lv_{topics}_{CURRENT_TIME}"
    else:
        name_model = name
        name_vis = name
    lda_model.save(f"output/lda_models/{name_model}.model")
    # print(lda_model.show_topics(formatted=True))

    vis = pyLDAvis.gensim_models.prepare(lda_model, bow_corpus, dictionary)
    path = f"output/ldavis/{name_vis}.html"
    pyLDAvis.save_html(vis, path)
    print(f"File created at {os.path.abspath(path)}")
