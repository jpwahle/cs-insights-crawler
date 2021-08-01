import os
import numpy as np
import pandas as pd

from nlpland.constants import COLUMN_ABSTRACT, MISSING_PAPERS, COLUMN_ABSTRACT_SOURCE, ABSTRACT_SOURCE_ANTHOLOGY, ABSTRACT_SOURCE_RULE


def print_null_values(df: pd.DataFrame, column: str) -> None:
    print(f"# null values in '{column}': {df[column].isnull().sum()}")


def print_possible_values(df: pd.DataFrame, column: str) -> None:
    print(f"Possible values in '{column}':")
    print(np.sort(df[column].unique()))


def check_dataset(df: pd.DataFrame) -> None:
    print("We first want to analyse the dataset and make sure everything is correct and as we expect it.")
    print(f"These are all the columns in the dataset: {df.columns.values}")
    print()

    print("For directory naming, when downloading the papers, we need to make sure certain columns do not contain null values.")
    print_null_values(df, 'AA year of publication')
    print_null_values(df, 'GS year of publication')
    print_possible_values(df, "AA year of publication")
    print("-> We will use 'AA year of publication'.")
    print()

    print_possible_values(df, 'NS venue name')
    print_null_values(df, 'NS venue name')
    print_possible_values(df, 'AA venue code')
    print_null_values(df, 'AA venue code')
    print("-> We will use 'NS venue name', because it is more readable.")
    print()

    print(f"The amount of not unique IDs in 'AA paper id': {len(df.index.unique()) - len(df.index)}")
    print()

    print(f"To download the papers we also need to check certain columns.")
    print_null_values(df, 'AA url')
    print()

    print(f"Over time more venues and their corresponding websites might get added.")
    known_websites = ("https://www.aclweb.org/anthology/", "http://www.lrec-conf.org/proceedings/",
                      "https://doi.org/", "http://doi.org/", "http://yanran.li/")
    print(f"Websites this code can download from: {known_websites}")
    problematic_urls = df[~df["AA url"].str.startswith(known_websites)]
    if len(problematic_urls.index) == 0:
        print("There are no problematic URLs.")
    else:
        print(f"The code might have issues with the following URLs:")
        print(problematic_urls['AA url'])
    print()

    print("How many papers does the dataset contain?")
    path_papers = os.getenv("PATH_PAPERS")
    downloaded = sum([len(files) for r, d, files in os.walk(path_papers)])
    print(f"Files downloaded: {downloaded}")
    dataset_size = len(df.index)
    print(f"Papers in dataset: {dataset_size}")
    df_missing = pd.read_csv(MISSING_PAPERS, delimiter="\t", low_memory=False, header=None)
    missing_papers = len(df_missing.index)
    print(f"Papers in {MISSING_PAPERS}: {missing_papers}")
    print(f"Unaccounted: {dataset_size - downloaded - missing_papers}")
    print()

    print("How many abstracts are already in the dataset?")
    if COLUMN_ABSTRACT in df.columns:
        abstracts = df[COLUMN_ABSTRACT].count()
        rows = len(df.index)
        anth = df[df[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_ANTHOLOGY][COLUMN_ABSTRACT_SOURCE].count()
        rule = df[df[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE][COLUMN_ABSTRACT_SOURCE].count()
        print(f"{abstracts} abstracts of {rows} papers: {abstracts/rows*100:.2f}%")
        print(f"{anth} abstracts were extracted from the anthology.")
        print(f"{rule} abstracts were extracted with the rule-based system.")
        print("The amount of abstracts per year we get from the anthology:")
        df2 = df[df[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_ANTHOLOGY]
        df3 = df[df[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE]
        df4 = pd.DataFrame()
        df4["total"] = df.groupby(["AA year of publication"]).count()["AA url"]
        df4["anth"] = df2.groupby(["AA year of publication"])[COLUMN_ABSTRACT].count()
        df4["rule"] = df3.groupby(["AA year of publication"])[COLUMN_ABSTRACT].count()
        print(df4)
        # print(pd.concat([years_total, years_anth, years_rule], axis=1))
    else:
        print("0. The column does not exist yet.")
    print()

    print("For further analysis we also might want to look into some other columns.")
    print_null_values(df, "AA first author full name")
    print("What entries in 'AA first author full name' do not have a ',':")
    print(df[~df['AA first author full name'].str.contains(',')]['AA first author full name'])


def check_encoding_issues(df: pd.DataFrame) -> None:
    df_enc = df[df[COLUMN_ABSTRACT].str.contains("�", na=False)]
    for index, row in df_enc.iterrows():
        print(index, row["AA year of publication"], row["NS venue name"])
        print(row[COLUMN_ABSTRACT])
    print(f"There are {len(df_enc.index)} abstracts with at least one �.")


def check_paper_parsing(paper_path: str) -> None:
    # full_path = "E:/nlp/NLP_Scholar_Papers/2012/COLING/C12-2031.pdf"
    from tika import parser
    raw = parser.from_file(paper_path)
    text = raw["content"]
    print(text)


def count_anthology_abstracts():
    from lxml import etree
    path_anthology = os.getenv("PATH_ANTHOLOGY")
    papers = 0
    abstracts = 0
    for file in os.listdir(path_anthology):
        if file.endswith(".xml"):
            tree = etree.parse(f"{path_anthology}/{file}")
            papers += tree.xpath('count(//paper)')
            abstracts += tree.xpath('count(//abstract)')
    print(f"ACL Anthology contains {int(papers)} papers with {int(abstracts)} abstracts.")
