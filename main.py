import os

import numpy as np
import pandas as pd
import urllib.request
from dotenv import load_dotenv
from tqdm import tqdm

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


def clean_paper_id(paper_id: str):
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str):
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


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
                    with open("missing_papers.txt", "a+") as f:
                        f.write(f"{row['AA paper id']}\t{url}\n")


def extract_abstracts(df: pd.DataFrame):
    failures = 0
    papers_checked = 0
    tops = 0
    nones = 0
    df = df[df["AA year of publication"] == 2010]
    top_tier = ["ACL", "EMNLP", "NAACL", "COLING", "EACL"]
    for i, row in tqdm(df.iterrows(), total=df.shape[0]):
        paper_id = clean_paper_id(row["AA paper id"])
        venue = clean_venue_name(row["NS venue name"])
        year = row["AA year of publication"]
        path_papers = os.getenv("PATH_PAPERS")
        full_path = f"{path_papers}/{year}/{venue}/{paper_id}.pdf"
        if os.path.isfile(full_path):
            papers_checked += 1
            from tika import parser

            raw = parser.from_file(full_path)

            # with open(full_path, 'rb', encoding='utf-8') as file:
            #     content = file.read()
            # raw = parser.from_buffer(content)

            text = raw["content"]
            if text is None:
                nones += 1
                # print("None", full_path)
            else:
                with open("tika.txt", "w+", encoding='utf-8') as f:
                    start_string = "Abstract"
                    pos_abstract = text.find(start_string)
                    if pos_abstract == -1:
                        start_string = "ABSTRACT"
                        pos_abstract = text.find(start_string)
                        if pos_abstract == -1:
                            start_string = "A b s t r a c t"
                            pos_abstract = text.find(start_string)
                    # pos_1 = text.find("\n1", pos_abstract)
                    # pos_intro = text.find("Introduction", pos_1)
                    #pos_1 = 1
                    pos_intro = text.find("\n1 Introduction", pos_abstract)
                    if pos_intro == -1:
                        pos_intro = text.find("\n1 Task Description", pos_abstract)
                        if pos_intro == -1:
                            pos_intro = text.find("\n1. Introduction", pos_abstract)
                            if pos_intro == -1:
                                pos_intro = text.find("\n\nIntroduction", pos_abstract)
                                if pos_intro == -1:
                                    pos_intro = text.find("\n\n1 ", pos_abstract)
                    start_pos = pos_abstract
                    end_pos = pos_intro
                    if row["NS venue name"] == "CL":
                        end_string = "\n\n1. Introduction"
                        end_pos = text.find(end_string)
                        start_string = "\n\n"
                        start_pos = text.rfind("\n\n", 0, end_pos)
                        #print(start_pos, end_pos)
                    #print(pos_abstract, pos_1, pos_intro)
                    if row["NS venue name"] in top_tier:
                        tops += 1
                        if (start_pos == -1 or end_pos == -1) and year >= 1980:
                            print("failure:", start_pos, end_pos, full_path)
                            # if full_path == "E:/nlp/NLP_Scholar_Papers/2001/SemEval/S01-1004.pdf":
                            #print(text)
                            failures += 1
                            if failures >= 100:
                                print(papers_checked, nones)
                                quit()
                        #print(text)
                    abstract = text[start_pos+len(start_string):end_pos]
                    # if row["NS venue name"] == "CL":
                    #     print(abstract)
                    # print(abstract)
                    #f.write(abstract)
    print(papers_checked, nones, failures, tops)

            #quit()

            # import textract
            # text = textract.process(full_path, encoding='utf-8', errors="ignore")
            # with open("textract.txt", "w+", encoding='utf-8', errors="ignore") as f:
            #     print(text)
            #     f.write(text)

            # import PyPDF2
            # pdf_file = open(full_path, 'rb')
            # read_pdf = PyPDF2.PdfFileReader(pdf_file)
            # number_of_pages = read_pdf.getNumPages()
            # with open("pypdf2.txt", "wb+") as f:
            #     for i2 in range(number_of_pages):
            #         page = read_pdf.getPage(i2)
            #         page_content = page.extractText()
            #         print(page_content.encode('utf-8'))
            #         f.write(page_content.encode('utf-8'))

            # import pdfplumber
            # pdf = pdfplumber.open(full_path)
            # page = pdf.pages[0]
            # text = page.extract_text()
            # print(text)
            # pdf.close()


if __name__ == '__main__':
    df = pd.read_csv(os.getenv("PATH_DATASET"), delimiter="\t", low_memory=False, header=0)
    # analyze_dataset(df)
    # download_papers(df, "2020")
    extract_abstracts(df)
