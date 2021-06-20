import pandas as pd
from collections import Counter
from nlpland.clean import clean_newline_hyphens_and_tokenize,  clean_newline_hyphens, get_english_words, get_stopwords_and_punct
from typing import List
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import nltk
from nltk import word_tokenize
import numpy as np
from nlpland.constants import COLUMN_ABSTRACT


def count_words_in_df(df: pd.DataFrame):
    counts = Counter()
    english_words = get_english_words()
    for index, row in df.iterrows():
        tokens = clean_newline_hyphens_and_tokenize(row["AA title"], english_words)
        if not pd.isna(row["NE abstract"]):
            tokens += clean_newline_hyphens_and_tokenize(row["NE abstract"], english_words)
        counts += Counter(tokens)
    stopwords = get_stopwords_and_punct()
    for stopword in stopwords:
        counts.pop(stopword, None)
    return counts


def count_bigrams_in_df(df: pd.DataFrame):
    counts = Counter()
    english_words = get_english_words()
    for index, row in df.iterrows():
        tokens = clean_newline_hyphens_and_tokenize(row["AA title"], english_words)
        bigrams = list(nltk.bigrams(tokens))
        if not pd.isna(row["NE abstract"]):
            tokens = clean_newline_hyphens_and_tokenize(row["NE abstract"], english_words)
            bigrams += list(nltk.bigrams(tokens))
        counts += Counter(bigrams)
    stopwords = get_stopwords_and_punct()
    for bigram in list(counts.keys()):
        if any(stopword in bigram for stopword in stopwords):
            counts.pop(bigram)
    return counts


def count_and_compare_words(k: int, df1: pd.DataFrame, df2: pd.DataFrame = None, n: int = 1):
    if n == 1:
        print(count_words_in_df(df1).most_common(k))
        if df2 is not None:
            print(count_words_in_df(df2).most_common(k))
    if n == 2:
        print(count_bigrams_in_df(df1).most_common(k))
        if df2 is not None:
            print(count_bigrams_in_df(df2).most_common(k))


def count_grams(documents: List[List[str]], n: int = 1, tfidf: bool = False):
    english_words = get_english_words()
    stopwords = get_stopwords_and_punct()
    cv = CountVectorizer(analyzer='word', tokenizer=word_tokenize,
                         preprocessor=lambda doc: clean_newline_hyphens(doc, english_words),
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
        if any(stopword in tokens for stopword in stopwords):
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


def plot_word_counts(df: pd.DataFrame, venues: str, venues2: str, years: str = None, years2: str = None):
    import scattertext as st

    english_words = get_english_words()
    df[COLUMN_ABSTRACT] = df[COLUMN_ABSTRACT].apply(lambda x: clean_newline_hyphens(x, english_words))

    df["parse"] = df[COLUMN_ABSTRACT].apply(st.whitespace_nlp_with_sentences)

    if years is None and years2 is None:
        category = venues
        category_col = "NS venue name"
    else:
        category = years
        category_col = "year"
    category_name = f"{venues} {years}"
    category_name2 = f"{venues2} {years2}"

    corpus = st.CorpusFromParsedDocuments(
        df, category_col=category_col, parsed_col="parse"
    ).build().get_unigram_corpus().compact(st.AssociationCompactor(2000))

    html = st.produce_scattertext_explorer(
        corpus,
        category=category, category_name=category_name, not_category_name=category_name2,
        minimum_term_frequency=5, pmi_threshold_coefficient=0,
        width_in_pixels=1000,
        transform=st.Scalers.dense_rank
    )
    html_file = f"output/st_wordcount.html"
    open(html_file, 'w+', encoding="UTF-8").write(html)
    print(f"File created at {html_file}")

    # import webbrowser
    # webbrowser.get("chrome").open_new_tab(html_file)
