if __name__ == '__main__':
    print("hello world")
    import pandas as pd
    df = pd.read_csv("NLP-Scholar-Data-vJune2020/nlp-scholar-papers-vJune2020.txt", delimiter="\t", low_memory=False, header=0)
    # df = df.drop(["AA in-volume id", "AA paper id", "AA doi", "AA collection id", "AA volume id", "AA venue code", "AA booktitle", "AA booktitle-url",
    #               "AA front matter Url", "NS tutorial flag", "NS demo flag", "NS student paper flag", "NS shared task flag", "NS workshop flag",
    #               "NS doctoral consortium flag", "NS main conference flag", "NS short paper flag", "NS long paper flag", "NS conference flag", "NS poster flag",
    #               "NS oral paper flag", "NS squib flag", "NS paper type", "NS title-year id", "GS venue info 1 (GS calls this journal)",
    #               "GS venue info 2 (GS calls this number)", "GS cid", "GS pubid", "GS masterpcid", "AA first author full name", "AA first author first name",
    #               "AA publisher", "NS companion flag", "GS title", "GS authors", "GS year of publication"], axis=1)
    #df = df.drop(["AA in-volume id", "AA paper id", "NS paper type", "NS title-year id"], axis=1)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 2000)
    pd.set_option("display.max_rows", 50, "display.max_columns", 5)
    df = df[["GS cid", "GS pubid", "GS masterpcid", "GS venue info 2 (GS calls this number)", "GS venue info 1 (GS calls this journal)"]]

    print(df)