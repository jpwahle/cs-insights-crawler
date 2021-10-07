"""This module includes multiple functions to analyze the consistency and amount of metadata
(especially abstracts) of a given dataset."""
import os

import numpy as np
import pandas as pd
from lxml import etree
from tika import parser

from nlpland.constants import (ABSTRACT_SOURCE_ANTHOLOGY, ABSTRACT_SOURCE_RULE,
                               COLUMN_ABSTRACT, COLUMN_ABSTRACT_SOURCE,
                               MISSING_PAPERS)


def print_null_values(column: pd.Series) -> None:
    """Print the amount of null (NA) values for a given column.

    Args:
        column: Column to evaluate.
    """
    print(f"# null values in '{column.name}': {column.isnull().sum()}")


def print_possible_values(column: pd.Series) -> None:
    """Print all distinct values of a given column.

    Args:
        column: Column to evaluate.
    """
    print(f"Possible values in '{column.name}':")
    print(np.sort(column.unique()))


def print_abstracts_per_year(df_papers: pd.DataFrame) -> None:
    """Count how many abstracts are in the dataset per year per abstract-source.

    Args:
        df_papers: Dataframe to evaluate.
    """
    print("How many abstracts are already in the dataset?")
    if COLUMN_ABSTRACT in df_papers.columns:
        abstracts = df_papers[COLUMN_ABSTRACT].count()
        rows = len(df_papers.index)
        anth = df_papers[
            df_papers[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_ANTHOLOGY
            ][COLUMN_ABSTRACT_SOURCE].count()
        rule = df_papers[df_papers[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE][
            COLUMN_ABSTRACT_SOURCE
        ].count()
        print(f"{abstracts} abstracts of {rows} papers: {abstracts/rows*100:.2f}%")
        print(f"{anth} abstracts were extracted from the anthology.")
        print(f"{rule} abstracts were extracted with the rule-based system.")
        print("The amount of abstracts per year we get from the anthology:")
        df_anth = df_papers[
            df_papers[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_ANTHOLOGY
            ]
        df_rule = df_papers[df_papers[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE]
        df_source = pd.DataFrame()
        df_source["total"] = df_papers.groupby(["AA year of publication"]).count()[
            "AA url"
        ]
        df_source["anth"] = df_anth.groupby(["AA year of publication"])[
            COLUMN_ABSTRACT
        ].count()
        df_source["rule"] = df_rule.groupby(["AA year of publication"])[
            COLUMN_ABSTRACT
        ].count()
        print(df_source)
        # print(pd.concat([years_total, years_anth, years_rule], axis=1))
    else:
        print("0. The column does not exist yet.")
    print()


def check_dataset(df_papers: pd.DataFrame) -> None:
    """Print various statistics about the the dataframe/dataset.

    Args:
        df_papers: Dataframe to evaluate.
    """
    print(
        "We first want to analyse the dataset and make sure everything is correct "
        "and as we expect it."
    )
    print(f"These are all the columns in the dataset: {df_papers.columns.values}")
    print()

    print(
        "For directory naming, when downloading the papers, we need to make sure certain columns "
        "do not contain null values."
    )
    print_null_values(df_papers["AA year of publication"])
    print_null_values(df_papers["GS year of publication"])
    print_possible_values(df_papers["AA year of publication"])
    print("-> We will use 'AA year of publication'.")
    print()

    print_possible_values(df_papers["NS venue name"])
    print_null_values(df_papers["NS venue name"])
    print_possible_values(df_papers["AA venue code"])
    print_null_values(df_papers["AA venue code"])
    print("-> We will use 'NS venue name', because it is more readable.")
    print()

    print(
        "The amount of not unique IDs in 'AA paper id': "
        f"{len(df_papers.index.unique()) - len(df_papers.index)}"
    )
    print()

    print("To download the papers we also need to check certain columns.")
    print_null_values(df_papers["AA url"])

    print()

    print("Over time more venues and their corresponding websites might get added.")
    known_websites = (
        "https://www.aclweb.org/anthology/",
        "http://www.lrec-conf.org/proceedings/",
        "https://doi.org/",
        "http://doi.org/",
        "http://yanran.li/",
    )
    print(f"Websites this code can download from: {known_websites}")
    problematic_urls = df_papers[~df_papers["AA url"].str.startswith(known_websites)]
    if len(problematic_urls.index) == 0:
        print("There are no problematic URLs.")
    else:
        print("The code might have issues with the following URLs:")
        print(problematic_urls["AA url"])
    print()

    print("How many papers does the dataset contain?")
    path_papers = os.getenv("PATH_PAPERS", "")
    downloaded = sum([len(files) for r, d, files in os.walk(path_papers)])
    print(f"Files downloaded: {downloaded}")
    dataset_size = len(df_papers.index)
    print(f"Papers in dataset: {dataset_size}")
    df_missing = pd.read_csv(
        MISSING_PAPERS, delimiter="\t", low_memory=False, header=None
    )
    missing_papers = len(df_missing.index)
    print(f"Papers in {MISSING_PAPERS}: {missing_papers}")
    print(f"Unaccounted: {dataset_size - downloaded - missing_papers}")
    print()

    print_abstracts_per_year(df_papers)

    print("For further analysis we also might want to look into some other columns.")
    print_null_values(df_papers["AA first author full name"])
    print("What entries in 'AA first author full name' do not have a ',':")
    print(
        df_papers[~df_papers["AA first author full name"].str.contains(",")][
            "AA first author full name"
        ]
    )


def check_encoding_issues(df_papers: pd.DataFrame) -> None:
    """Print all papers, which abstracts contain a '�' symbol.

    Args:
        df_papers: Dataframe to evaluate.
    """
    df_enc = df_papers[df_papers[COLUMN_ABSTRACT].str.contains("�", na=False)]
    for index, row in df_enc.iterrows():
        print(index, row["AA year of publication"], row["NS venue name"])
        print(row[COLUMN_ABSTRACT])
    print(f"There are {len(df_enc.index)} abstracts with at least one �.")


def check_paper_parsing(paper_path: str) -> None:
    """Parse a specific paper with tika and print its output.

    Args:
        paper_path: Filepath to the paper to check.
    """
    # full_path = "E:/nlp/NLP_Scholar_Papers/2012/COLING/C12-2031.pdf"
    raw = parser.from_file(paper_path)
    text = raw["content"]
    print(text)


def count_anthology_abstracts() -> None:
    """Print the amount of abstracts in the ACL Anthology XML files."""
    path_anthology = os.getenv("PATH_ANTHOLOGY")
    papers = 0
    abstracts = 0
    for file in os.listdir(path_anthology):
        if file.endswith(".xml"):
            tree = etree.parse(f"{path_anthology}/{file}")
            papers += tree.xpath("count(//paper)")
            abstracts += tree.xpath("count(//abstract)")
    print(
        f"ACL Anthology contains {int(papers)} papers with {int(abstracts)} abstracts."
    )
