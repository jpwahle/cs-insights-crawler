import os
import pandas as pd
import nlpland.clean as clean
from typing import List
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from nlpland.constants import COLUMN_ABSTRACT, CURRENT_TIME
import nlpland.filter as filter

CATEGORY = "category"
PARSE = "parse"


def preprocess_dfs(df1: pd.DataFrame, df2:pd.DataFrame):
    df1[CATEGORY] = "c1"
    df2[CATEGORY] = "c2"
    df = pd.concat([df1, df2])

    english_words = clean.english_words()

    df_titles = df[[CATEGORY, "AA title"]].rename(columns={"AA title": PARSE})
    df_abstracts = df[[CATEGORY, COLUMN_ABSTRACT]]
    df_abstracts = df_abstracts.dropna(subset=[COLUMN_ABSTRACT])
    df_abstracts[COLUMN_ABSTRACT] = df_abstracts[COLUMN_ABSTRACT].apply(lambda x: clean.newline_hyphens(x, english_words))
    df_abstracts = df_abstracts.rename(columns={COLUMN_ABSTRACT: PARSE})
    df = pd.concat([df_titles, df_abstracts])

    # df[PARSE] = df[COLUMN_ABSTRACT].apply(st.whitespace_nlp)
    # the above one is faster, but breaks if lemmatization is active
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat", "custom"])
    df[PARSE] = df[PARSE].apply(nlp)
    # TODO add download for spacy model
    # TODO add title column as words
    return df


def plot_word_counts(df1: pd.DataFrame, df2: pd.DataFrame, filters):
    import scattertext as st
    df = preprocess_dfs(df1, df2)
    stopwords = clean.stopwords_and_more()

    corpus = st.CorpusFromParsedDocuments(
        df, category_col=CATEGORY, parsed_col=PARSE,
        feats_from_spacy_doc=st.FeatsFromSpacyDoc(use_lemmas=True)
    ).build().remove_terms(stopwords, ignore_absences=True).get_unigram_corpus().compact(
        st.AssociationCompactor(2000))

    html = st.produce_scattertext_explorer(
        corpus,
        category="c1", category_name=filter.category_names(filters),
        not_category_name=filter.category_names(filters, second_df=True),
        minimum_term_frequency=5, pmi_threshold_coefficient=0,
        width_in_pixels=1000,
        transform=st.Scalers.dense_rank
    )
    path = f"output/scattertext_{CURRENT_TIME}.html"
    open(path, 'w+', encoding="UTF-8").write(html)
    print(f"File created at {os.path.abspath(path)}")
