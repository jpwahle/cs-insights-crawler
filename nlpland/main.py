import os
import time
import numpy as np
import pandas as pd
import urllib.request
from dotenv import load_dotenv
from tqdm import tqdm
from tika import parser
from typing import List

load_dotenv()

MISSING_PAPERS = "missing_papers.txt"
ABSTRACT_COLUMN = "NE abstract"
UNICODE_COLUMN = "NE encoding issue flag"
NA = "NA"


def print_null_values(df: pd.DataFrame, column: str) -> None:
    print(f"# null values in '{column}': {df[column].isnull().sum()}")


def print_possible_values(df: pd.DataFrame, column: str) -> None:
    print(f"Possible values in '{column}':")
    print(np.sort(df[column].unique()))


def analyze_dataset(df: pd.DataFrame) -> None:
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
    if ABSTRACT_COLUMN in df.columns:
        abstracts = df[ABSTRACT_COLUMN].count()
        rows = len(df.index)
        print(f"{abstracts} abstracts of {rows} papers: {abstracts/rows*100:.2f}%")
    else:
        print("0. The column does not exist yet.")
    print("")

    print("For further analysis we also might want to look into some other columns.")
    print_null_values(df, "AA first author full name")
    print("What entries in 'AA first author full name' do not have a ',':")
    print(df[~df['AA first author full name'].str.contains(',')]['AA first author full name'])


def clean_paper_id(paper_id: str) -> str:
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str) -> str:
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


def download_papers(df: pd.DataFrame, min_year: int, max_year: int) -> None:
    path_papers = os.getenv("PATH_PAPERS")
    df_missing = pd.read_csv(MISSING_PAPERS, delimiter="\t", low_memory=False, header=None)

    years = []
    for year in range(min_year, max_year+1):
        years.append(year)

    for year in years:
        print(f"Downloading papers from {year}.")
        df_year = df[df["AA year of publication"] == year]
        for i, row in tqdm(df_year.iterrows(), total=df_year.shape[0]):
            venue = clean_venue_name(row["NS venue name"])
            output_dir = f"{path_papers}/{year}/{venue}"
            os.makedirs(output_dir, exist_ok=True)
            filename = clean_paper_id(row["AA paper id"])
            full_path = f"{output_dir}/{filename}.pdf"

            if not os.path.isfile(full_path) and row["AA paper id"] not in df_missing.iloc[:, [0]].values:
                url = row["AA url"]
                if str.startswith(url, "https://www.aclweb.org/anthology/"):
                    url = f"{url}.pdf"
                elif str.startswith(url, "http://yanran.li/"):
                    # TODO
                    pass

                # print(url, full_path)
                try:
                    urllib.request.urlretrieve(url, full_path)
                except urllib.error.HTTPError:
                    with open(MISSING_PAPERS, "a+") as f:
                        f.write(f"{row['AA paper id']}\t{url}\n")


def save_dataset(df: pd.DataFrame):
    path_dataset_expanded = os.getenv("PATH_DATASET_EXPANDED")
    df.to_csv(path_dataset_expanded, index=False, sep="\t", na_rep=NA)


def determine_earliest_string(text: str, possible_strings: List[str]):
    earliest_string = ""
    earliest_pos = -1
    for possible_string in possible_strings:
        pos_current = text.find(possible_string)
        if pos_current != -1 and (earliest_pos == -1 or pos_current < earliest_pos):
            earliest_pos = pos_current
            earliest_string = possible_string
    return earliest_pos, earliest_string


def extract_abstracts(df: pd.DataFrame, min_year: int = 1965, max_year: int = 2020, venues: List[str] = None, overwrite_abstracts: bool = False) -> None:
    # TODO startup tika server
    start = time.time()
    iterated = 0
    searched = 0
    skipped = 0
    index = 0
    nones = 0
    unicode = 0
    no_file = 0
    path_papers = os.getenv("PATH_PAPERS")

    if ABSTRACT_COLUMN not in df.columns:
        df[ABSTRACT_COLUMN] = None
    if UNICODE_COLUMN not in df.columns:
        df[UNICODE_COLUMN] = False

    df_select = df[(min_year <= df["AA year of publication"]) & (df["AA year of publication"] <= max_year)]
    if venues is not None:
        df_select = df_select[df_select["NS venue name"].isin(venues)]

    for i, row in tqdm(df_select.iterrows(), total=df_select.shape[0]):
        iterated += 1
        if overwrite_abstracts or pd.isnull(row[ABSTRACT_COLUMN]):
            paper_id = clean_paper_id(row["AA paper id"])
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
                    start_strings = ["Abstract", "ABSTRACT", "A b s t r a c t"]
                    start_pos, start_string = determine_earliest_string(text, start_strings)
                    start_pos += len(start_string)

                    end_strings_1 = ["\n\nTITLE AND ABSTRACT IN ", "\n\nTitle and Abstract in ", "KEYWORDS:", "Keywords:"]
                    end_pos, end_string = determine_earliest_string(text, end_strings_1)
                    if end_pos == -1:
                        end_strings_2 = ["\n\n1 Introduction", "\n\n1. Introduction",
                                         "\n\n1 Task Description", "\n\n1. Task Description",
                                         "\n\nIntroduction\n\n", "\n\n1 "]
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
                        index += 1
                    else:
                        abstract = text[start_pos:end_pos]
                        df.loc[i, ABSTRACT_COLUMN] = abstract
                        if "�" in abstract:
                            df.loc[i, UNICODE_COLUMN] = True
                            unicode += 1
                        else:
                            df.loc[i, UNICODE_COLUMN] = False
            else:
                no_file += 1
        else:
            skipped += 1
        if i % 1000 == 0 and i > 0:
            save_dataset(df)
    save_dataset(df)
    print(f"Papers iterated: {iterated} matching year+venue")
    print(f"Abstracts searched: {searched} abstracts searched")
    print(f"Abstracts skipped: {skipped} already existed")
    print(f"none: {nones} texts of papers are None")
    print(f"index: {index} abstracts not found")
    print(f"�: {unicode} new abstracts with �")
    print(f"no_file: {no_file} papers not downloaded")
    duration = time.gmtime(time.time()-start)
    print(f"This took {time.strftime('%Mm %Ss', duration)}.")


def paper_stats(df: pd.DataFrame):
    path_papers = os.getenv("PATH_PAPERS")
    # import os
    cpt = sum([len(files) for r, d, files in os.walk(path_papers)])
    print(f"Files downloaded: {cpt}")
    dataset_size = len(df.index)
    print(f"Papers in dataset: {dataset_size}")
    df_missing = pd.read_csv(MISSING_PAPERS, delimiter="\t", low_memory=False, header=None)
    missing_papers = len(df_missing.index)
    print(f"Papers in missing_papers.txt: {missing_papers}")
    print(f"Unaccounted: {dataset_size - cpt - missing_papers}")


def print_unicode_to_file(df: pd.DataFrame) -> None:
    df_uni = df[df[UNICODE_COLUMN] == True]
    for i, row in df_uni.iterrows():
        print(row["AA year of publication"], row["NS venue name"], row["AA paper id"])
        print(row["NE abstract"])


def check_paper_text() -> None:
    full_path = "E:/nlp/NLP_Scholar_Papers/2012/COLING/C12-2031.pdf"
    raw = parser.from_file(full_path)
    text = raw["content"]
    print(text)
    print(text.find("ABSTRACT\n"))


if __name__ == '__main__':
    df_main = pd.read_csv(os.getenv("PATH_DATASET"), delimiter="\t", low_memory=False, header=0)
    df_expanded = pd.read_csv(os.getenv("PATH_DATASET_EXPANDED"), delimiter="\t", low_memory=False, header=0)
    analyze_dataset(df_expanded)
    # check_paper_text()
    # download_papers(df_main, 1965, 2020)
    # extract_abstracts(df_main, False)
    top_tier = ["ACL", "EMNLP", "NAACL", "COLING", "EACL"]
    # top_tier = ["COLING"]
    # top_tier = None
    # extract_abstracts(df_expanded, min_year=2010, venues=top_tier, overwrite_abstracts=False)
    # paper_stats(df_main)
    # print_unicode_to_file(df_expanded)
