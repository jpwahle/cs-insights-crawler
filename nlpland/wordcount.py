import pandas as pd
from collections import Counter
# import nltk
from nltk.corpus import stopwords
import nltk
from nlpland.data_cleanup import clean_and_tokenize
from string import punctuation
from typing import List
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer
from nltk import word_tokenize
from nltk.corpus import stopwords, words
from nlpland.data_cleanup import clean_newline_hyphens
import numpy as np

def count_words_in_df(df: pd.DataFrame):
    counts = Counter()
    english_dict = set(words.words())
    for index, row in df.iterrows():
        tokens = clean_and_tokenize(row["AA title"], english_dict)
        if not pd.isna(row["NE abstract"]):
            tokens += clean_and_tokenize(row["NE abstract"], english_dict)
        counts += Counter(tokens)
    stopwords_ = set(stopwords.words('english'))
    for stopword in stopwords_:
        counts.pop(stopword, None)
    for char in punctuation:
        counts.pop(char, None)
    return counts


def count_bigrams_in_df(df: pd.DataFrame):
    counts = Counter()
    english_dict = set(words.words())
    for index, row in df.iterrows():
        tokens = clean_and_tokenize(row["AA title"], english_dict)
        bigrams = list(nltk.bigrams(tokens))
        if not pd.isna(row["NE abstract"]):
            tokens = clean_and_tokenize(row["NE abstract"], english_dict)
            bigrams += list(nltk.bigrams(tokens))
        counts += Counter(bigrams)
    stopwords_ = set(stopwords.words('english'))
    for bigram in list(counts.keys()):
        if any(stopword in bigram for stopword in stopwords_) or any(punc in bigram for punc in punctuation):
            counts.pop(bigram)
    return counts


def count_and_compare_words(k: int, df1: pd.DataFrame, df2: pd.DataFrame = None):
    print(count_words_in_df(df1).most_common(k))
    if df2 is not None:
        print(count_words_in_df(df2).most_common(k))


def count_and_compare_bigrams(k: int, df1: pd.DataFrame, df2: pd.DataFrame = None):
    print(count_bigrams_in_df(df1).most_common(k))
    if df2 is not None:
        print(count_bigrams_in_df(df2).most_common(k))


def count_grams(documents: List[List[str]], n: int = 1, tfidf: bool = False):
    english_dict = set(words.words())
    stops = stopwords.words('english')
    stops += [char for char in punctuation]
    cv = CountVectorizer(analyzer='word', tokenizer=word_tokenize,
                         preprocessor=lambda doc: clean_newline_hyphens(doc, english_dict),
                         lowercase=True, ngram_range=(n, n)
                         )
    # the sklearn tokenizer splits "open-source", nltk does not
    word_counts_matrix = cv.fit_transform(documents)  # is a sparse matrix

    word_counts = word_counts_matrix.sum(axis=0).tolist()[0]
    if tfidf:
        tfidf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
        tfidf_scores = tfidf_transformer.fit(word_counts_matrix).idf_

    feature_names = cv.get_feature_names()
    for token in cv.get_feature_names():
        tokens = token.split(" ")
        if any(stopword in tokens for stopword in stops):
            index = feature_names.index(token)
            feature_names.pop(index)
            word_counts.pop(index)
            if tfidf:
                np.delete(tfidf_scores, index)
    if tfidf:
        return feature_names, word_counts, tfidf_scores
    else:
        return feature_names, word_counts


def get_most_common_grams(k: int, documents: List[List[str]], n: int = 1):
    feature_names, word_counts, tfidf_scores = count_grams(documents, n, tfidf=True)
    freqs = zip(feature_names, word_counts, tfidf_scores)
    return sorted(freqs, key=lambda x: x[1], reverse=True)[:k]


def count_and_compare(k: int, documents: List[List[str]], documents2: List[List[str]] = None, n: int = 1):
    print(get_most_common_grams(k, documents, n))
    if documents2 is not None:
        print(get_most_common_grams(k, documents2, n))
