import os

import pandas as pd
from gensim.models import FastText

import nlpland.data.clean as clean_

# from gensim.test.utils import common_texts  # some example sentences
from nlpland.constants import COLUMN_ABSTRACT, COLUMN_ABSTRACT_SOURCE, CURRENT_TIME

SIZE = 100
ITER = 10


def semantic(df_abstracts: pd.DataFrame, train: bool, name: str) -> None:
    if name is None:
        name = f"ft_{SIZE}_{ITER}_{CURRENT_TIME}"
    if train:
        df_abstracts = df_abstracts[
            df_abstracts[COLUMN_ABSTRACT_SOURCE] == "anthology"
        ][COLUMN_ABSTRACT]
        # print(common_texts[0])
        # ['human', 'interface', 'computer']
        # print(len(common_texts))
        # 9
        # model = FastText(size=4, window=3, min_count=1)  # instantiate
        # model.build_vocab(sentences=common_texts)
        # model.train(sentences=common_texts, total_examples=len(common_texts), epochs=10)  # train
        print("start preprocess")
        vocabulary = clean_.english_words()
        lemmatizer = clean_.get_lemmatizer()
        stopwords = clean_.stopwords_and_more()
        df_abstracts = df_abstracts.apply(
            lambda row: clean_.preprocess_text(row, vocabulary, lemmatizer, stopwords)
        )
        print("start train")
        model = FastText(
            size=SIZE, window=3, min_count=1, sentences=list(df_abstracts), iter=ITER
        )
        print("finish train")

        path = f"output/fasttext_models/{name}.model"
        model.save(path)
        print(f"File created at {os.path.abspath(path)}")
    model = FastText.load(f"output/fasttext_models/{name}.model")

    print(
        model.wv.most_similar_cosmul(
            positive=["computer", "human"], negative=["interface"]
        )
    )
    # print(model.wv.doesnt_match("human computer interface tree".split()))
    print(model.wv.similarity("computer", "human"))
    # print(model.wv.similarity('computer', 'interface'))
    # print(model.wv.similarity('interface', 'human'))
    print(model.wv.similarity("computer", "processor"))
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


# def plot(df_papers: pd.DataFrame) -> None:
#     # digits = load_digits()
#     # mapper = umap.UMAP().fit(digits.data)
#     # print(digits.target)
#     # print(digits)
#     # umap.plot.points(mapper, labels=digits.target)
#     # plt.show()
#
#     model = FastText.load("fasttext.model")
