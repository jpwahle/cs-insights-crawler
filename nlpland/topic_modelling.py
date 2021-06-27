import os
import pandas as pd

from nlpland.constants import COLUMN_ABSTRACT
from nlpland.clean import preprocess_text, get_stopwords_and_more, get_english_words, get_lemmatizer
from nlpland.constants import CURRENT_TIME

import gensim
import pyLDAvis.gensim_models


def topic(df: pd.DataFrame, topics: int, load: bool):
    english_words = get_english_words()
    stopwords = get_stopwords_and_more()
    lemmatizer = get_lemmatizer()
    processed_docs = df[COLUMN_ABSTRACT].apply(lambda abstract: preprocess_text(abstract, english_words, lemmatizer, stopwords))

    dictionary = gensim.corpora.Dictionary(processed_docs)
    bow_corpus = [dictionary.doc2bow(doc) for doc in processed_docs]

    if load:
        lda_model = gensim.models.LdaModel.load("output/ldamodel")
    else:
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
