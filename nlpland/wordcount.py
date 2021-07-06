import os
import pandas as pd
import nlpland.clean as clean
from typing import List
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from nlpland.constants import COLUMN_ABSTRACT, CURRENT_TIME
import nlpland.filter as filter


def generate_token_matrices(documents: List[List[str]], n: int = 1):
    english_words = clean.english_words()
    stopwords = clean.stopwords_and_more()
    lemmatizer = clean.lemmatizer()
    vectorizer = CountVectorizer(analyzer='word',
                                 tokenizer=lambda doc: clean.remove_stopwords(clean.tokenize_and_lemmatize(doc, lemmatizer), stopwords),
                                 preprocessor=lambda doc: clean.newline_hyphens(doc, english_words),
                                 lowercase=True,
                                 ngram_range=(n, n)
                                 )
    # the sklearn tokenizer splits "open-source", nltk does not
    counts_matrix = vectorizer.fit_transform(documents)  # is a sparse matrix
    tfidf_matrix = TfidfTransformer(smooth_idf=True, use_idf=True).fit(counts_matrix)

    return vectorizer.get_feature_names(), counts_matrix, tfidf_matrix


def count_tokens(k: int, documents: List[List[str]], n: int = 1):
    feature_names, counts_matrix, tfidf_matrix = generate_token_matrices(documents, n)
    word_counts = counts_matrix.sum(axis=0).tolist()[0]
    tfidf_scores = tfidf_matrix.idf_
    freqs = list(zip(feature_names, word_counts, tfidf_scores))
    highest_count = sorted(freqs, key=lambda x: x[1], reverse=True)[:k]
    highest_tfidf = sorted(freqs, key=lambda x: x[2], reverse=True)[:k]
    return highest_count, highest_tfidf


def plot_word_counts(df: pd.DataFrame, filters):
    import scattertext as st

    english_words = clean.english_words()
    stopwords = clean.stopwords_and_more()
    df[COLUMN_ABSTRACT] = df[COLUMN_ABSTRACT].apply(lambda x: clean.newline_hyphens(x, english_words))

    # df["parse"] = df[COLUMN_ABSTRACT].apply(st.whitespace_nlp)
    # the above one is faster, but breaks if lemmatization is active
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat", "custom"])
    df["parse"] = df[COLUMN_ABSTRACT].apply(nlp)
    # TODO add download for spacy model
    # TODO add title column as words

    corpus = st.CorpusFromParsedDocuments(
        df, category_col="category", parsed_col="parse",
        feats_from_spacy_doc=st.FeatsFromSpacyDoc(use_lemmas=True)
    ).build().remove_terms(stopwords, ignore_absences=True).get_unigram_corpus().compact(st.AssociationCompactor(2000))

    html = st.produce_scattertext_explorer(
        corpus,
        category="c1", category_name=filter.category_names(filters), not_category_name=filter.category_names(filters, second_df = True),
        minimum_term_frequency=5, pmi_threshold_coefficient=0,
        width_in_pixels=1000,
        transform=st.Scalers.dense_rank
    )
    path = f"output/scattertext_{CURRENT_TIME}.html"
    open(path, 'w+', encoding="UTF-8").write(html)
    print(f"File created at {os.path.abspath(path)}")
