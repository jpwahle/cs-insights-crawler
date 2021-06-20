import pandas as pd
from collections import Counter
from nlpland.data_cleanup import clean_newline_hyphens_and_tokenize,  clean_newline_hyphens
from string import punctuation
from typing import List
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords, words
import numpy as np
from nlpland.constants import COLUMN_ABSTRACT

def count_words_in_df(df: pd.DataFrame):
    counts = Counter()
    english_dict = set(words.words())
    for index, row in df.iterrows():
        tokens = clean_newline_hyphens_and_tokenize(row["AA title"], english_dict)
        if not pd.isna(row["NE abstract"]):
            tokens += clean_newline_hyphens_and_tokenize(row["NE abstract"], english_dict)
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
        tokens = clean_newline_hyphens_and_tokenize(row["AA title"], english_dict)
        bigrams = list(nltk.bigrams(tokens))
        if not pd.isna(row["NE abstract"]):
            tokens = clean_newline_hyphens_and_tokenize(row["NE abstract"], english_dict)
            bigrams += list(nltk.bigrams(tokens))
        counts += Counter(bigrams)
    stopwords_ = set(stopwords.words('english'))
    for bigram in list(counts.keys()):
        if any(stopword in bigram for stopword in stopwords_) or any(punc in bigram for punc in punctuation):
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


def plot_word_counts(df: pd.DataFrame, venues: str, venues2: str, years: str = None, years2: str = None):
    import scattertext as st

    english_dict = set(words.words())
    df[COLUMN_ABSTRACT] = df[COLUMN_ABSTRACT].apply(lambda x: clean_newline_hyphens(x, english_dict))

    df["parse"] = df[COLUMN_ABSTRACT].apply(st.whitespace_nlp_with_sentences)

    if years is None and years2 is None:
        category = venues
        category_col = "NS venue name"
        category_name = venues
        category_name2 = venues2
    else:
        category = years
        category_col = "year"
        category_name = years
        category_name2 = years2

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
    html_file = f"./data/wordcount.html"
    open(html_file, 'w+', encoding="UTF-8").write(html)
    print(f"File created at {html_file}")

    # import webbrowser
    # webbrowser.get("chrome").open_new_tab(html_file)
