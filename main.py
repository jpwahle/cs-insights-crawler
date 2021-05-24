import os

import numpy as np
import pandas as pd
import urllib.request
from dotenv import load_dotenv

def analyze_cols(df: pd.DataFrame):
    #df = df.drop(["AA in-volume id", "AA paper id", "AA doi", "AA collection id", "AA volume id", "AA venue code", "AA booktitle", "AA booktitle-url",
                  # "AA front matter Url", "NS tutorial flag", "NS demo flag", "NS student paper flag", "NS shared task flag", "NS workshop flag",
                  # "NS doctoral consortium flag", "NS main conference flag", "NS short paper flag", "NS long paper flag", "NS conference flag", "NS poster flag",
                  # "NS oral paper flag", "NS squib flag", "NS paper type", "NS title-year id", "GS venue info 1 (GS calls this journal)",
                  # "GS venue info 2 (GS calls this number)", "GS cid", "GS pubid", "GS masterpcid", "AA first author full name", "AA first author first name",
                  # "AA publisher", "NS companion flag", "GS title", "GS authors", "GS year of publication"], axis=1)
    # df = df.drop(["AA in-volume id", "AA paper id", "NS paper type", "NS title-year id"], axis=1)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 2000)
    pd.set_option("display.max_rows", 50, "display.max_columns", 5)
    # df = df[["GS cid", "GS pubid", "GS masterpcid", "GS venue info 2 (GS calls this number)", "GS venue info 1 (GS calls this journal)"]]
    print(df)

    cols = df.columns.values
    cols = pd.Series(cols)
    print(list(cols))

    # Directory naming:
    print(df["AA year of publication"].isnull().sum())
    print(df["GS year of publication"].isnull().sum())
    # -> use AA year of publication, because there are not empty values compared to GS

    print(np.sort(df["AA venue code"].unique()))
    print(np.sort(df["NS venue name"].unique()))
    print(df["AA venue code"].isnull().sum())
    print(df["NS venue name"].isnull().sum())
    # -> Use NS venue name, because it is more readable for humans and is not null for every entry

    print(df["AA url"].isnull().sum())
    # no missing

    years = np.sort(df["AA year of publication"].unique())
    print(years)

    print(df["AA url"].str.extractall(
        r"(^(?!https:\/\/www\.aclweb\.org\/anthology\/|http:\/\/www\.lrec-conf\.org\/proceedings\/|http(s)?:\/\/doi\.org\/).*)"))

    print(df["AA first author full name"].isnull().sum())
    print(df[~df["AA first author full name"].str.contains(",")]["AA first author full name"])
    #print(df["AA first author full name"])

    print(len(df["AA paper id"].unique()))

    # == 52289
    #print(df["AA paper id"].unique().sum())


def download_papers(df: pd.DataFrame, years: str):
    path_papers = os.getenv("PATH_PAPERS")

    # df = df[["AA year of publication", "NS venue name", "AA url", "AA title", "AA first author full name"]]

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
        df2 = df[df["AA year of publication"] == year]
        for i, row in df2.iterrows():
            venue = row["NS venue name"]
            venue = venue.replace("*", "").replace("/", "_").replace(" ", "_")
            # author = row["AA first author full name"].split(",")[0]
            # author = author.replace(" ", "_")
            # title = row["AA title"].replace(" ", "_")
            # filename = f"{author}_{title}.pdf"
            output_dir = f"{path_papers}/{year}/{venue}"
            os.makedirs(output_dir, exist_ok=True)
            filename = row["AA paper id"].replace(".", "_")
            full_path = f"{output_dir}/{filename}.pdf"

            if not os.path.isfile(full_path):
                # TODO also check missing papers
                url = row["AA url"]
                if str.startswith(url, "https://www.aclweb.org/anthology/"):
                    url = f"{url}.pdf"
                elif str.startswith(url, "https://doi.org/") or str.startswith(url, "http://doi.org/") or str.startswith(url, "http://www.lrec-conf.org/proceedings/"):
                    pass
                elif str.startswith(url, "http://yanran.li/"):
                    pass
                else:
                    print(url)

                print(url, full_path)
                try:
                    urllib.request.urlretrieve(url, full_path)
                except urllib.error.HTTPError:
                    with open("missing_papers.txt", "a+") as f:
                        f.write(f"{row['AA paper id']}\t{url}\n")


if __name__ == '__main__':
    print("running!")
    load_dotenv()
    df = pd.read_csv("NLP-Scholar-Data-vJune2020/nlp-scholar-papers-vJune2020.txt", delimiter="\t", low_memory=False, header=0)
   # analyze_cols(df)
    download_papers(df, "1971-1975")
