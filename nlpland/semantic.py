import pandas as pd
from gensim.models import FastText
# from gensim.test.utils import common_texts  # some example sentences
from nlpland.constants import COLUMN_ABSTRACT, COLUMN_ABSTRACT_SOURCE
import nlpland.clean as clean


def semantic(df_abstracts: pd.DataFrame, train: bool = False):
    if train:
        df_abstracts = df_abstracts[df_abstracts[COLUMN_ABSTRACT_SOURCE] == "anthology"][COLUMN_ABSTRACT]
        # print(common_texts[0])
        # ['human', 'interface', 'computer']
        # print(len(common_texts))
        # 9
        # model = FastText(size=4, window=3, min_count=1)  # instantiate
        # model.build_vocab(sentences=common_texts)
        # model.train(sentences=common_texts, total_examples=len(common_texts), epochs=10)  # train
        print("start preprocess")
        vocabulary = clean.english_words()
        lemmatizer = clean.lemmatizer()
        stopwords = clean.stopwords_and_more()
        df_abstracts = df_abstracts.apply(lambda row: clean.preprocess_text(row, vocabulary, lemmatizer, stopwords))  # todo
        print("start train")
        model = FastText(size=100, window=3, min_count=1, sentences=list(df_abstracts), iter=10)
        print("finish train")
        # TODO sentences not documents

        model.save("fasttext.model")
    model = FastText.load("fasttext.model")

    print(model.wv.most_similar_cosmul(positive=['computer', 'human'], negative=['interface']))
    # print(model.wv.doesnt_match("human computer interface tree".split()))
    print(model.wv.similarity('computer', 'human'))
    # print(model.wv.similarity('computer', 'interface'))
    # print(model.wv.similarity('interface', 'human'))
    print(model.wv.similarity('computer', 'processor'))
    print(model.wv.similarity("neural", "network"))
    print(model.wv.similarity("cnn", "rnn"))
    print(model.wv.similarity("english", "language"))

    # print()

    # print(model.wv.similar_by_word("human"))
    # print(model.wv.similar_by_word("computer"))
    # print(model.wv.similar_by_word("network"))
    # print(model.wv.similar_by_word("neural network"))
    # print(model.wv.similar_by_word("neural-network"))
    # print(model.wv.similar_by_word("ai"))
    # print(model.wv.similar_by_word("foreign language"))
    # print(model.wv.similar_by_word("foreign-language"))
    # print(model.wv.similar_by_word("translation"))


def plot(df: pd.DataFrame):
    import umap
    from sklearn.datasets import load_digits
    import umap.plot
    import matplotlib.pyplot as plt

    # digits = load_digits()
    # mapper = umap.UMAP().fit(digits.data)
    # print(digits.target)
    # print(digits)
    # umap.plot.points(mapper, labels=digits.target)
    # plt.show()

    model = FastText.load("fasttext.model")