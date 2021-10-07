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
    print(type(tfidf_matrix))
    print(type(counts_matrix))

    return vectorizer.get_feature_names(), counts_matrix, tfidf_matrix


def token_frequencies(df_papers: pd.DataFrame, ngrams: str) -> pd.DataFrame:
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
    df_freq = token_frequencies(df_papers, ngrams)
    count_top = df_freq.sort_values(by=["tf"], ascending=False).head(k)
    tfidf_top = df_freq.sort_values(by=["tfidf"], ascending=False).head(k)
    return count_top, tfidf_top


def counts_over_time(
    df_papers: pd.DataFrame,
    k: int,
    ngrams: str,
    name: str,
    tfidf: bool,
    filters: Dict[str, FILTER_DATATYPES],
) -> None:
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
        count_top = token_frequencies(df_year, ngrams).sort_values(
            by=[mode], ascending=False
        )
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
