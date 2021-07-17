import os
import pandas as pd
import nlpland.clean as clean
from typing import List
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from nlpland.constants import COLUMN_ABSTRACT, CURRENT_TIME
import nlpland.filter as filter

CATEGORY = "category"
PARSE = "parse"


def preprocess_df(df: pd.DataFrame, filters):
    venues = filters["venues"]
    year = filters["year"]
    min_year = filters["min_year"]
    max_year = filters["max_year"]
    author = filters["author"]
    venues2 = filters["venues2"]
    year2 = filters["year2"]
    min_year2 = filters["min_year2"]
    max_year2 = filters["max_year2"]
    author2 = filters["author2"]

    venues_list = filter.venues_to_list(venues)
    venues_list2 = filter.venues_to_list(venues2)

    if venues_list != venues_list2:
        df[CATEGORY] = df.apply(lambda row: filter.category_venues(row, venues_list), axis=1)
    elif year != year2 or min_year != min_year2 or max_year != max_year2:
        df[CATEGORY] = df.apply(lambda row: filter.category_years(row, year, min_year, max_year), axis=1)
    elif author != author2:
        df[CATEGORY] = df.apply(lambda row: filter.category_authors(row, author), axis=1)

    english_words = clean.english_words()

    df_titles = df[[CATEGORY, "AA title"]].rename(columns={"AA title": PARSE})
    df_abstracts = df[[CATEGORY, COLUMN_ABSTRACT]]
    df_abstracts = df_abstracts.dropna(subset=[COLUMN_ABSTRACT])
    df_abstracts[COLUMN_ABSTRACT] = df_abstracts[COLUMN_ABSTRACT].apply(lambda x: clean.newline_hyphens(x, english_words))
    df_abstracts = df_abstracts.rename(columns={COLUMN_ABSTRACT: PARSE})
    df_full = pd.concat([df_titles, df_abstracts])

    # df[PARSE] = df[COLUMN_ABSTRACT].apply(st.whitespace_nlp)
    # the above one is faster, but breaks if lemmatization is active
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat", "custom"])
    df_full[PARSE] = df_full[PARSE].apply(nlp)
    # TODO add download for spacy model
    # TODO add title column as words
    return df_full


def plot_word_counts(df: pd.DataFrame, filters):
    import scattertext as st
    df = preprocess_df(df, filters)
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
