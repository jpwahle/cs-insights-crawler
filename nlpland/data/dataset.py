"""This module offers functions to create the dataset (download papers, extract abstracts), save and
load it."""
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from typing import List, Tuple, Dict
from lxml import etree


import pandas as pd
import tika
from tika import parser
from tqdm import tqdm

# from collections import defaultdict

from nlpland.constants import (
    ABSTRACT_SOURCE_ANTHOLOGY,
    ABSTRACT_SOURCE_RULE,
    COLUMN_ABSTRACT,
    COLUMN_ABSTRACT_SOURCE,
    MISSING_PAPERS,
    START_STRINGS,
    END_STRINGS_1,
    END_STRINGS_2,
)
from nlpland.data.clean import clean_paper_id, clean_venue_name


def download_papers(df_papers: pd.DataFrame) -> None:
    """Download papers given the links in a Dataframe.

    Args:
        df_papers: Dataframe with the link to the papers and other metadata.
    """
    path_papers = os.getenv("PATH_PAPERS")
    df_missing = pd.read_csv(MISSING_PAPERS, delimiter="\t", low_memory=False, header=None)

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

            if not os.path.isfile(full_path) and index not in df_missing.iloc[:, [0]].values:
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


def determine_earliest_string(text: str, possible_strings: List[str]) -> Tuple[int, str]:
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


def print_results_extract_abstracts_rulebased(
    count_dict: Dict[str, int], duration: Tuple[int, int, int, int, int, int, int, int, int]
) -> None:
    """Prints the results of the abstract extraction methods.

    Args:
        count_dict: Dict containing all counts
        duration: Duration the procedure took

    Returns:
        None
    """
    print(f"Papers iterated: {count_dict['iterated']} matching filters")
    print(
        f"Abstracts searched: {count_dict['searched']} abstracts searched"
    )
    print(f"Abstracts skipped: {count_dict['skipped']} already existed")
    print(f"none: {count_dict['nones']} texts of papers are None")
    print(f"index: {count_dict['index_err']} abstracts not found")
    print(f"no_file: {count_dict['no_file']} papers not downloaded")
    print(f"long_abstract: {count_dict['long_abstracts']} papers with (too) long abstracts")
    print(f"This took {time.strftime('%Mm %Ss', duration)}.")


def helper_abstracts_rulebased(
    index: str, count_dict: Dict[str, int], path_papers: str, df_full: pd.DataFrame
) -> pd.DataFrame:
    """Helper function for the abstract extraction method

    Args:
        index: The current index.
        count_dict: Dict to count everything
        path_papers: Path to the downloaded papers.
        df_full: Dataframe containing all relevant information for extraction

    Returns:
        Tuple of earliest position of a string and earliest occurring string.
    """
    paper_id = clean_paper_id(index)
    venue = clean_venue_name(df_full.at[index, "NS venue name"])
    year = df_full.at[index, "AA year of publication"]

    full_path = f"{path_papers}/{year}/{venue}/{paper_id}.pdf"

    if os.path.isfile(full_path):
        count_dict["searched"] += 1

        text: str = parser.from_file(full_path)["content"]

        if text is None:
            count_dict["nones"] += 1
        else:
            start_pos, start_string = determine_earliest_string(text, START_STRINGS)
            start_pos += len(start_string)

            end_pos, end_string = determine_earliest_string(text, END_STRINGS_1)
            if end_pos == -1:
                for end_string in END_STRINGS_2:
                    end_pos = text.find(end_string, start_pos)
                    if end_pos != -1:
                        break

            # if row["NS venue name"] == "CL":
            #     end_string = "\n\n1. Introduction"
            #     end_pos = text.find(end_string)
            #     start_string = "\n\n"
            #     start_pos = text.rfind("\n\n", 0, end_pos)

            if end_pos == -1 or start_pos == -1:
                count_dict["index_err"] += 1
            else:
                abstract = text[start_pos:end_pos]  # pylint: disable=E1136
                df_full.at[index, COLUMN_ABSTRACT] = abstract
                df_full.at[index, COLUMN_ABSTRACT_SOURCE] = ABSTRACT_SOURCE_RULE
                if len(abstract) > 5000:
                    count_dict["long_abstract"] += 1
    else:
        count_dict["no_file"] += 1

    return df_full


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
    count_dict: dict = defaultdict(int)

    path_papers = os.getenv("PATH_PAPERS", default="")
    tika.initVM()

    for index, row in tqdm(df_select.iterrows(), total=df_select.shape[0]):
        count_dict["iterated"] += 1
        if (overwrite_rule and row[COLUMN_ABSTRACT_SOURCE] == ABSTRACT_SOURCE_RULE) or pd.isnull(
            row[COLUMN_ABSTRACT]
        ):
            df_full = helper_abstracts_rulebased(index, count_dict, path_papers, df_full)
        else:
            count_dict["skipped"] += 1
        if count_dict["iterated"] % 1000 == 0 and count_dict["iterated"] > 0:
            save_dataset(df_full)
    save_dataset(df_full)
    duration = time.gmtime(time.time() - start)
    print_results_extract_abstracts_rulebased(count_dict, duration)


def helper_abstracts_anthology(
    volume,
    df_papers: pd.DataFrame,
    counter_dict: Dict[str, int],
    collection_id: str,
    volume_id: str,
) -> Tuple[Dict[str, int], pd.DataFrame]:
    """Extract the abstract of papers from PDF files based on a defined set of rules.

    This function will never overwrite abstracts extracted from the anthology itself. It can be set
    to overwrite abstracts previously extracted with this rule-based system/function that are also
    in the selection "df_select".

    Args:
        volume: The current volume.
        df_papers: The full dataset of papers for statistical purposes.
        counter_dict: The count dict for all counts.
        collection_id: The current collection id.
        volume_id: The current volume id.
    """
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
                df_papers.at[paper_id, COLUMN_ABSTRACT_SOURCE] = ABSTRACT_SOURCE_ANTHOLOGY
                counter_dict["abstracts"] += 1
            else:
                counter_dict["unknown_id"] += 1
        else:
            counter_dict["no_id_abstract"] += 1

    return counter_dict, df_papers


def extract_abstracts_anthology(df_papers: pd.DataFrame) -> None:
    """Extract abstract from the ACL Anthology XML files.

    This always overwrites the abstracts for all papers which have an abstract in the XML files.

    Args:
        df_papers: Dataframe of the papers to match the entries in the XML files against.
    """
    start = time.time()
    count_dict: dict = defaultdict(int)
    path_anthology = os.getenv("PATH_ANTHOLOGY")
    for file in tqdm(os.listdir(path_anthology), total=len(os.listdir(path_anthology))):
        assert file is not None
        if file.endswith(".xml"):
            tree = etree.parse(  # pylint: disable=I1101
                os.path.join(path_anthology, file)  # type: ignore
            )
            for collection in tree.iter("collection"):
                collection_id = collection.attrib["id"]
                for volume in collection.iter("volume"):
                    if len(volume.attrib) > 0:
                        volume_id = volume.attrib["id"]
                        count_dict, df_papers = helper_abstracts_anthology(
                            volume, df_papers, count_dict, collection_id, volume_id
                        )
    save_dataset(df_papers)
    print(f"Abstracts added/overwritten: {count_dict['abstracts']}")
    duration = time.gmtime(time.time() - start)
    print(f"This took {time.strftime('%Mm %Ss', duration)}.")
