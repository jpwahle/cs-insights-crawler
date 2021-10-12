"""This module offers functions to create the dataset (download papers, extract abstracts), save and
load it."""
import os
import time
import urllib.request
from typing import List, Tuple
from lxml import etree

import pandas as pd
import tika
from tika import parser
from tqdm import tqdm

from nlpland.constants import (
    ABSTRACT_SOURCE_ANTHOLOGY,
    ABSTRACT_SOURCE_RULE,
    COLUMN_ABSTRACT,
    COLUMN_ABSTRACT_SOURCE,
    MISSING_PAPERS,
)
from nlpland.data.clean import clean_paper_id, clean_venue_name


def download_papers(df_papers: pd.DataFrame) -> None:
    """Download papers given the links in a Dataframe.

    Args:
        df_papers: Dataframe with the link to the papers and other metadata.
    """
    path_papers = os.getenv("PATH_PAPERS")
    df_missing = pd.read_csv(
        MISSING_PAPERS, delimiter="\t", low_memory=False, header=None
    )

    years = sorted(df_papers["AA year of publication"].unique())
    for year in years:
        print(f"Downloading papers from {year}.")
        df_year = df_papers[df_papers["AA year of publication"] == year]
        for index, row in tqdm(df_year.iterrows(), total=df_year.shape[0]):
            venue = clean_venue_name(row["NS venue name"])
            output_dir = f"{path_papers}/{year}/{venue}"
            os.makedirs(output_dir, exist_ok=True)
            filename = clean_paper_id(index)
            full_path = f"{output_dir}/{filename}.pdf"

            if (
                not os.path.isfile(full_path)
                and index not in df_missing.iloc[:, [0]].values
            ):
                url = row["AA url"]
                if str.startswith(url, "https://www.aclweb.org/anthology/"):
                    url = f"{url}.pdf"
                elif str.startswith(url, "http://yanran.li/"):
                    pass
                try:
                    urllib.request.urlretrieve(url, full_path)
                except urllib.error.HTTPError:
                    with open(MISSING_PAPERS, "a+", encoding="utf-8") as file:
                        file.write(f"{index}\t{url}\n")


def load_dataset(original_dataset: bool) -> pd.DataFrame:
    """Load the original unedited dataset or the expanded one.

    Args:
        original_dataset: If True, load the original dataset, otherwise the expanded one.

    Returns:
        Dataset as Dataframe.
    """
    if original_dataset:
        env_var_name = "PATH_DATASET"
    else:
        env_var_name = "PATH_DATASET_EXPANDED"

    return pd.read_csv(
        os.getenv(env_var_name), delimiter="\t", low_memory=False, header=0, index_col=0
    )


def save_dataset(df_papers: pd.DataFrame) -> None:
    """Save the given dataset:

    This overwrites the expanded dataset, if its already exists.

    Args:
        df_papers: Dataframe to save.
    """
    path_dataset_expanded = os.getenv("PATH_DATASET_EXPANDED")
    df_papers.to_csv(path_dataset_expanded, sep="\t", na_rep="NA")


def determine_earliest_string(
    text: str, possible_strings: List[str]
) -> Tuple[int, str]:
    """Determine the earliest occurrence of any of the given list of strings as a substring in
     another string.

    Args:
        text: Text to search the substrings in.
        possible_strings: List of string to search in "text".

    Returns:
        Tuple of earliest position of a string and earliest occurring string.
    """
    earliest_string = ""
    earliest_pos = -1
    for possible_string in possible_strings:
        pos_current = text.find(possible_string)
        if pos_current != -1 and (earliest_pos == -1 or pos_current < earliest_pos):
            earliest_pos = pos_current
            earliest_string = possible_string
    return earliest_pos, earliest_string


def extract_abstracts_rulebased(
    df_select: pd.DataFrame, df_full: pd.DataFrame, overwrite_rule: bool = False
) -> None:
    """Extract the abstract of papers from PDF files based on a defined set of rules.

    This function will never overwrite abstracts extracted from the anthology itself. It can be set
    to overwrite abstracts previously extracted with this rule-based system/function that are also
    in the selection "df_select".

    Args:
        df_select: The dataset of papers to extract abstract from.
        df_full: The full dataset of papers for statistical purposes.
        overwrite_rule: If True, overwrites abstracts previously extracted with this function.
    """
    start = time.time()
    iterated = 0
    searched = 0
    skipped = 0
    index_err = 0
    nones = 0
    no_file = 0
    long_abstract = 0
    path_papers = os.getenv("PATH_PAPERS")

    tika.initVM()

    for index, row in tqdm(df_select.iterrows(), total=df_select.shape[0]):
        iterated += 1
        if (
            overwrite_rule and row[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE
        ) or pd.isnull(row[COLUMN_ABSTRACT]):
            paper_id = clean_paper_id(index)
            venue = clean_venue_name(row["NS venue name"])
            year = row["AA year of publication"]
            full_path = f"{path_papers}/{year}/{venue}/{paper_id}.pdf"
            if os.path.isfile(full_path):
                searched += 1

                raw = parser.from_file(full_path)
                text = raw["content"]

                if text is None:
                    nones += 1
                else:
                    start_strings = [
                        "Abstract ",
                        "Abstract\n",
                        "ABSTRACT ",
                        "ABSTRACT\n",
                        "A b s t r a c t ",
                        "A b s t r a c t\n",
                    ]
                    start_pos, start_string = determine_earliest_string(
                        text, start_strings
                    )
                    start_pos += len(start_string)

                    end_strings_1 = [
                        "\n\nTITLE AND ABSTRACT IN ",
                        "\n\nTitle and Abstract in ",
                        "KEYWORDS:",
                        "Keywords:",
                        "Keywords :",
                        "KEYWORDS :",
                    ]
                    end_pos, end_string = determine_earliest_string(text, end_strings_1)
                    if end_pos == -1:
                        end_strings_2 = [
                            "\n\n1 Introduction",
                            "\n\n1. Introduction",
                            "\n\n1 Task Description",
                            "\n\n1. Task Description",
                            "\n\nIntroduction\n\n",
                            "\n\n1 ",
                            "\n\n1. ",
                        ]
                        for end_string in end_strings_2:
                            end_pos = text.find(end_string, start_pos)
                            if end_pos != -1:
                                break

                    # if row["NS venue name"] == "CL":
                    #     end_string = "\n\n1. Introduction"
                    #     end_pos = text.find(end_string)
                    #     start_string = "\n\n"
                    #     start_pos = text.rfind("\n\n", 0, end_pos)

                    if end_pos == -1 or start_pos == -1:
                        index_err += 1
                    else:
                        abstract = text[start_pos:end_pos]
                        df_full.at[index, COLUMN_ABSTRACT] = abstract
                        df_full.at[index, COLUMN_ABSTRACT_SOURCE] = ABSTRACT_SOURCE_RULE
                        if len(abstract) > 5000:
                            long_abstract += 1
            else:
                no_file += 1
        else:
            skipped += 1
        if iterated % 1000 == 0 and iterated > 0:
            save_dataset(df_full)
    save_dataset(df_full)
    print(f"Papers iterated: {iterated} matching filters")
    print(f"Abstracts searched: {searched} abstracts searched")
    print(f"Abstracts skipped: {skipped} already existed")
    print(f"none: {nones} texts of papers are None")
    print(f"index: {index_err} abstracts not found")
    print(f"no_file: {no_file} papers not downloaded")
    print(f"long_abstract: {no_file} papers with (too) long abstracts")
    duration = time.gmtime(time.time() - start)
    print(f"This took {time.strftime('%Mm %Ss', duration)}.")


def extract_abstracts_anthology(df_papers: pd.DataFrame) -> None:
    """Extract abstract from the ACL Anthology XML files.

    This always overwrites the abstracts for all papers which have an abstract in the XML files.

    Args:
        df_papers: Dataframe of the papers to match the entries in the XML files against.
    """
    start = time.time()
    abstracts = 0
    unknown_id = 0
    no_id_abstract = 0
    path_anthology = os.getenv("PATH_ANTHOLOGY")
    for file in tqdm(os.listdir(path_anthology), total=len(os.listdir(path_anthology))):
        if file.endswith(".xml"):
            tree = etree.parse(f"{path_anthology}/{file}")
            for collection in tree.iter("collection"):
                collection_id = collection.attrib["id"]
                for volume in collection.iter("volume"):
                    if len(volume.attrib) > 0:
                        volume_id = volume.attrib["id"]
                    else:
                        volume_id = ""
                    for paper in volume.iter("paper"):
                        children = paper.getchildren()
                        paper_id = None
                        abstract = None
                        for child in children:
                            if child.tag == "url":
                                if "http" not in child.text:
                                    paper_id = child.text
                            if child.tag == "abstract":
                                if child.text is not None:
                                    abstract = str(child.xpath("string()"))
                        if paper_id is None:
                            paper_id = paper.attrib["id"]
                            paper_id = f"{collection_id}-{volume_id}-{paper_id}"

                        if paper_id is not None and abstract is not None:
                            if paper_id in df_papers.index:
                                df_papers.at[paper_id, COLUMN_ABSTRACT] = abstract
                                df_papers.at[
                                    paper_id, COLUMN_ABSTRACT_SOURCE
                                ] = ABSTRACT_SOURCE_ANTHOLOGY
                                abstracts += 1
                            else:
                                unknown_id += 1
                        else:
                            no_id_abstract += 1
    save_dataset(df_papers)
    print(f"Abstracts added/overwritten: {abstracts}")
    duration = time.gmtime(time.time() - start)
    print(f"This took {time.strftime('%Mm %Ss', duration)}.")
