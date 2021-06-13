import pandas as pd
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nlpland.data_cleanup import clean_and_tokenize
from string import punctuation
from nltk.corpus import words


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
