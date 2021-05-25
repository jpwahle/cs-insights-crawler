import os

import numpy as np
import pandas as pd
import urllib.request
from dotenv import load_dotenv

load_dotenv()


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


def download_papers(df: pd.DataFrame, years: str):
    path_papers = os.getenv("PATH_PAPERS")
    df_missing = pd.read_csv("missing_papers.txt", delimiter="\t", low_memory=False, header=None)

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
        for i, row in df_year.iterrows():
            venue = row["NS venue name"]
            venue = venue.replace("*", "").replace("/", "_").replace(" ", "_")
            output_dir = f"{path_papers}/{year}/{venue}"
            os.makedirs(output_dir, exist_ok=True)
            filename = row["AA paper id"].replace(".", "_")
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
                    with open("missing_papers.txt", "a+") as f:
                        f.write(f"{row['AA paper id']}\t{url}\n")


if __name__ == '__main__':
    df = pd.read_csv(os.getenv("PATH_DATASET"), delimiter="\t", low_memory=False, header=0)
    # analyze_dataset(df)
    download_papers(df, "2010")
