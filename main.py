import os

import numpy as np
import pandas as pd
import urllib.request
from dotenv import load_dotenv
from tqdm import tqdm
from tika import parser

load_dotenv()

missing_papers = "missing_papers.txt"
abstract_col = "NE abstract"

def print_null_values(df: pd.DataFrame, column: str):
    print(f"# null values in '{column}': {df[column].isnull().sum()}")


def print_possible_values(df: pd.DataFrame, column: str):
    print(f"Possible values in '{column}':")
    print(np.sort(df[column].unique()))


def analyze_dataset(df: pd.DataFrame):
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

    print("For further analysis we also might want to look into some other columns.")
    print_null_values(df, "AA first author full name")
    print("What entries in 'AA first author full name' do not have a ',':")
    print(df[~df['AA first author full name'].str.contains(',')]['AA first author full name'])


def clean_paper_id(paper_id: str):
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str):
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


def download_papers(df: pd.DataFrame, years: str):
    path_papers = os.getenv("PATH_PAPERS")
    df_missing = pd.read_csv(missing_papers, delimiter="\t", low_memory=False, header=None)

    if "-" in years:
        years = years.split("-")
        min_year = int(years[0])
        max_year = int(years[1])
        years = []
        for year in range(min_year, max_year+1):
            if year not in years:
                years.append(year)
    else:
        years = [int(years)]

    for year in years:
        df_year = df[df["AA year of publication"] == year]
        for i, row in tqdm(df_year.iterrows()):
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

                print(url, full_path)
                try:
                    urllib.request.urlretrieve(url, full_path)
                except urllib.error.HTTPError:
                    with open(missing_papers, "a+") as f:
                        f.write(f"{row['AA paper id']}\t{url}\n")


def extract_abstracts(df: pd.DataFrame):
    iterated = 0
    searched = 0
    index = 0
    nones = 0
    unicode = 0
    path_papers = os.getenv("PATH_PAPERS")

    df = df[df["AA year of publication"] >= 2010]
    top_tier = ["ACL", "EMNLP", "NAACL", "COLING", "EACL"]
    df = df[df["NS venue name"].isin(top_tier)]

    # if abstract_col not in df.columns:
    #     df[abstract_col] = "NA"
    # else:
    #     df = df[df["NS venue name"].isin(top_tier)]

    for i, row in tqdm(df.iterrows(), total=df.shape[0]):
        iterated += 1
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
                print("None: ", full_path)
            else:
                #with open("tika.txt", "w+", encoding='utf-8') as f:
                start_strings = ["Abstract", "ABSTRACT", "A b s t r a c t"]
                start_string = ""
                start_pos = -1
                for start_string in start_strings:
                    start_pos = text.find(start_string)
                    if start_pos != -1:
                        break

                end_strings = ["\n\n1 Introduction", "\n\n1. Introduction", "\n\n1 Task Description", "\n\n1. Task Description", "\n\n1 "]
                end_pos = -1
                for end_string in end_strings:
                    end_pos = text.find(end_string, start_pos)
                    if end_pos != -1:
                        if end_string == "\n\n1. Task Description":
                            print(f"end string: 1. Task Description, {full_path}")
                            # TODO remove
                        break

                if row["NS venue name"] == "CL":
                    end_string = "\n\n1. Introduction"
                    end_pos = text.find(end_string)
                    start_string = "\n\n"
                    start_pos = text.rfind("\n\n", 0, end_pos)

                if start_pos == -1 or end_pos == -1:
                    print("index:", start_pos, end_pos, full_path)
                    index += 1
                    abstract = "NA"
                else:
                    abstract = text[start_pos+len(start_string):end_pos]

                if "�" in abstract:
                    unicode += 1

                #f.write(abstract)

    print(f"iterated: {iterated}, searched: {searched}, none: {nones}, index: {index}, �: {unicode}")


def check_paper():
    full_path = ""
    raw = parser.from_file(full_path)
    text = raw["content"]
    print(text)


if __name__ == '__main__':
    df = pd.read_csv(os.getenv("PATH_DATASET"), delimiter="\t", low_memory=False, header=0)
    # analyze_dataset(df)
    # download_papers(df, "2017-2019")
    extract_abstracts(df)
