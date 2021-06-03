import os
import numpy as np
import pandas as pd
from tika import parser

from nlpland.constants import COLUMN_ABSTRACT, MISSING_PAPERS


def print_null_values(df: pd.DataFrame, column: str) -> None:
    print(f"# null values in '{column}': {df[column].isnull().sum()}")


def print_possible_values(df: pd.DataFrame, column: str) -> None:
    print(f"Possible values in '{column}':")
    print(np.sort(df[column].unique()))


def analyse_dataset(df: pd.DataFrame) -> None:
    print("We first want to analyse the dataset and make sure everything is correct and as we expect it.")
    print(f"These are all the columns in the dataset: {df.columns.values}")
    print("")

    print("For directory naming, when downloading the papers, we need to make sure certain columns do not contain null values.")
    print_null_values(df, 'AA year of publication')
    print_null_values(df, 'GS year of publication')
    print_possible_values(df, "AA year of publication")
    print("-> We will use 'AA year of publication'.")
    print("")

    print_possible_values(df, 'NS venue name')
    print_null_values(df, 'NS venue name')
    print_possible_values(df, 'AA venue code')
    print_null_values(df, 'AA venue code')
    print("-> We will use 'NS venue name', because it is more readable.")
    print("")

    print(f"The amount of not unique IDs in 'AA paper id': {len(df['AA paper id'].unique()) - len(df.index)}")
    print("")

    print(f"To download the papers we also need to check certain columns.")
    print_null_values(df, 'AA url')
    print("")

    print(f"Over time more venues and their corresponding websites might get added.")
    known_websites = ("https://www.aclweb.org/anthology/", "http://www.lrec-conf.org/proceedings/",
                      "https://doi.org/", "http://doi.org/", "http://yanran.li/")
    print(f"Websites this code can download from: {known_websites}")
    problematic_urls = df[~df["AA url"].str.startswith(known_websites)]
    print(f"The code might have issues with the following URLs:")
    print(problematic_urls['AA url'])
    print("")

    print("How many abstracts are already in the dataset?")
    if COLUMN_ABSTRACT in df.columns:
        abstracts = df[COLUMN_ABSTRACT].count()
        rows = len(df.index)
        print(f"{abstracts} abstracts of {rows} papers: {abstracts/rows*100:.2f}%")
    else:
        print("0. The column does not exist yet.")
    print("")

    print("For further analysis we also might want to look into some other columns.")
    print_null_values(df, "AA first author full name")
    print("What entries in 'AA first author full name' do not have a ',':")
    print(df[~df['AA first author full name'].str.contains(',')]['AA first author full name'])


def paper_stats(df: pd.DataFrame):
    path_papers = os.getenv("PATH_PAPERS")
    downloaded = sum([len(files) for r, d, files in os.walk(path_papers)])
    print(f"Files downloaded: {downloaded}")
    dataset_size = len(df.index)
    print(f"Papers in dataset: {dataset_size}")
    df_missing = pd.read_csv(MISSING_PAPERS, delimiter="\t", low_memory=False, header=None)
    missing_papers = len(df_missing.index)
    print(f"Papers in missing_papers.txt: {missing_papers}")
    print(f"Unaccounted: {dataset_size - downloaded - missing_papers}")


def encoding_issues_to_file(df: pd.DataFrame) -> None:
    df_enc = df[df[COLUMN_ABSTRACT].str.contains("�")]
    for i, row in df_enc.iterrows():
        print(row["AA year of publication"], row["NS venue name"], row["AA paper id"])
        print(row["NE abstract"])


def check_paper_text() -> None:
    full_path = "E:/nlp/NLP_Scholar_Papers/2012/COLING/C12-2031.pdf"
    raw = parser.from_file(full_path)
    text = raw["content"]
    print(text)
    print(text.find("ABSTRACT\n"))


def count_anthology_abstracts():
    from lxml import etree
    df = pd.DataFrame()
    path_anthology = os.getenv("PATH_ANTHOLOGY")
    for conference in os.listdir(path_anthology):
        if conference.endswith(".xml"):
            tree = etree.parse(f"{path_anthology}/{conference}")
            tag = tree.xpath("volume/meta/year")
            if len(tag) > 0:
                papers = 0
                abstracts = 0
                for elem in tree.iter("paper"):
                    papers += 1
                for elem in tree.iter("abstract"):
                    abstracts += 1
                df2 = pd.DataFrame([[conference, papers, abstracts]])
                df = df.append(df2)
    print(f"papers: {df['papers'].sum()}, abstracts: {df['abstracts'].sum()}")

