import os
import pandas as pd

from nlpland.constants import COLUMN_ABSTRACT
import nlpland.clean as clean
from nlpland.constants import CURRENT_TIME

import gensim
import pyLDAvis.gensim_models


def topic(df: pd.DataFrame, topics: int):
    # TODO add title column for words
    english_words = clean.english_words()
    stopwords = clean.stopwords_and_more()
    lemmatizer = clean.lemmatizer()
    processed_docs = list(df[COLUMN_ABSTRACT].apply(lambda abstract: clean.preprocess_text(abstract, english_words, lemmatizer, stopwords)))
    # print(processed_docs)
    # quit()

    dictionary = gensim.corpora.Dictionary(processed_docs)
    bow_corpus = [dictionary.doc2bow(doc) for doc in processed_docs]

    lda_model = gensim.models.LdaMulticore(bow_corpus,
                                           num_topics=topics,
                                           id2word=dictionary,
                                           passes=10,
                                           workers=2)
    lda_model.save("output/ldamodel")
    print(lda_model.show_topics(formatted=True))

    vis = pyLDAvis.gensim_models.prepare(lda_model, bow_corpus, dictionary)
    path = f"output/ldavis_{CURRENT_TIME}.html"
    pyLDAvis.save_html(vis, path)
    print(f"File created at {os.path.abspath(path)}")
