import os
import pandas as pd

from nlpland.constants import COLUMN_ABSTRACT
import nlpland.clean as clean
from nlpland.constants import CURRENT_TIME

import gensim
import pyLDAvis.gensim_models


def topic(df: pd.DataFrame, topics: int):
    print("Preprocess docs")
    english_words = clean.english_words()
    stopwords = clean.stopwords_and_more()
    lemmatizer = clean.lemmatizer()
    abstracts = df[COLUMN_ABSTRACT].dropna()
    titles = df["AA title"].dropna()
    cleaned_abstracts = list(abstracts.apply(lambda text: clean.preprocess_text(text, english_words, lemmatizer, stopwords)))
    cleaned_titles = list(titles.apply(lambda text: clean.preprocess_text(text, english_words, lemmatizer, stopwords)))
    cleaned_docs = cleaned_titles + cleaned_abstracts

    print("Create model")
    dictionary = gensim.corpora.Dictionary(cleaned_docs)
    bow_corpus = [dictionary.doc2bow(doc) for doc in cleaned_docs]

    lda_model = gensim.models.LdaMulticore(bow_corpus,
                                           num_topics=topics,
                                           id2word=dictionary,
                                           passes=10,
                                           workers=2)
    print("Save model and results")
    lda_model.save(f"output/ldamodel_{topics}_{CURRENT_TIME}.model")
    print(lda_model.show_topics(formatted=True))

    vis = pyLDAvis.gensim_models.prepare(lda_model, bow_corpus, dictionary)
    path = f"output/ldavis_{topics}_{CURRENT_TIME}.html"
    pyLDAvis.save_html(vis, path)
    print(f"File created at {os.path.abspath(path)}")
