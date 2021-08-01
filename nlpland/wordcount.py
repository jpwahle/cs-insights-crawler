import pandas as pd
import numpy as np
import nlpland.clean as clean
import nlpland.filter as filter
from typing import List
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from nlpland.constants import COLUMN_ABSTRACT


def generate_token_matrices(documents: List[List[str]], n_lower: int, n_upper: int):
    english_words = clean.english_words()
    stopwords = clean.stopwords_and_more()
    lemmatizer = clean.lemmatizer()
    vectorizer = CountVectorizer(analyzer='word',
                                 tokenizer=lambda doc: clean.remove_stopwords(clean.tokenize_and_lemmatize(doc, lemmatizer), stopwords),
                                 preprocessor=lambda doc: clean.newline_hyphens(doc, english_words),
                                 lowercase=True,
                                 ngram_range=(n_lower, n_upper)
                                 )
    # the sklearn tokenizer splits "open-source", nltk does not
    counts_matrix = vectorizer.fit_transform(documents)  # is a sparse matrix
    tfidf_matrix = TfidfTransformer(smooth_idf=True, use_idf=True).fit(counts_matrix)

    return vectorizer.get_feature_names(), counts_matrix, tfidf_matrix


def token_frequencies(df: pd.DataFrame, ngrams: str):
    ngrams_list = filter.attributes_to_list(ngrams)
    if len(ngrams_list) > 1:
        n_upper = ngrams_list[1]
    else:
        n_upper = ngrams_list[0]

    documents = list(df[COLUMN_ABSTRACT].dropna()) + list(df["AA title"].dropna())
    feature_names, counts_matrix, tfidf_matrix = generate_token_matrices(documents, int(ngrams_list[0]), int(n_upper))
    tf = np.asarray(counts_matrix.sum(axis=0))[0]
    idf = tfidf_matrix.idf_
    frequencies = list(zip(feature_names, tf, tf * idf))
    return frequencies


def top_k_tokens(k: int, df: pd.DataFrame, ngrams: str):
    frequencies = token_frequencies(df, ngrams)
    count_top = sorted(frequencies, key=lambda x: x[1], reverse=True)[:k]
    tfidf_top = sorted(frequencies, key=lambda x: x[2], reverse=True)[:k]
    return count_top, tfidf_top
