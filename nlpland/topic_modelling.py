import pandas as pd

from nlpland.constants import COLUMN_ABSTRACT
from nlpland.clean import clean_newline_hyphens_and_tokenize, remove_stopwords, get_stopwords_and_punct, get_english_words

import gensim
import pyLDAvis.gensim_models


def topic(df: pd.DataFrame, topics: int, load: bool):
    english_words = get_english_words()
    stopwords = get_stopwords_and_punct()
    processed_docs = df[COLUMN_ABSTRACT].apply(lambda abstract: remove_stopwords(clean_newline_hyphens_and_tokenize(abstract, english_words), stopwords))

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
    pyLDAvis.save_html(vis, "output/ldavis.html")
