import click

import nlpland.dataset as data
import nlpland.data_cleanup as clean
import nlpland.data_check as check
import nlpland.wordcount as count_
from dotenv import load_dotenv

load_dotenv()


def get_dataset(original: bool):
    if original:
        return data.load_dataset("PATH_DATASET")
    else:
        return data.load_dataset("PATH_DATASET_EXPANDED")


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--min-year')
@click.option('--max-year')
def download(min_year, max_year):
    df = get_dataset(True)
    data.download_papers(df, min_year=min_year, max_year=max_year)


@cli.command()
@click.argument('mode', type=str)
@click.option('--original', is_flag=True)
@click.option('--overwrite', is_flag=True)
@click.option('--min-year')
@click.option('--max-year')
def extract(mode, original, overwrite, min_year, max_year):
    df = get_dataset(original)

    modes = ["rule", "anth"]
    if mode not in modes:
        print(f"Unsupported mode '{mode}'. Choose from {modes}.")
    if mode == "rule":
        data.extract_abstracts_rulebased(df, overwrite_abstracts=overwrite, min_year=min_year, max_year=max_year)
    elif mode == "anth":
        data.extract_abstracts_anthology(df)


@cli.command()
def checkencode():
    df = get_dataset(False)
    check.check_encoding_issues(df)


@cli.command()
@click.option('--original', is_flag=True)
def checkdataset(original):
    df = get_dataset(original)
    check.check_dataset(df)


@cli.command()
@click.argument('paper-path', type=str)
def checkpaper(paper_path):
    check.check_paper_parsing(paper_path)


@cli.command()
def countabstractsanth():
    check.count_anthology_abstracts()


@cli.command()
def grobid():
    from grobid_client.grobid_client import GrobidClient
    import time
    import os
    start = time.time()
    client = GrobidClient(config_path="C:/Users/Lennart/Desktop/grobid_client_python/config.json")
    path = "C:/test_papers"
    if os.path.isdir(path):
        print(f"Processing {len(os.listdir(path))} files.")
    client.process("processFulltextDocument", path, output="./resources/test_out_heavy/", n=20)
    print(f"This took {time.time()-start}s.")


@cli.command()
@click.argument('k', type=int)
@click.option('--venue1')
@click.option('--year1', type=int)
@click.option('--venue2')
@click.option('--year2', type=int)
def count(k: int, venue1: str, year1: int, venue2: str, year2: int):
    df1 = get_dataset(False)
    if venue1 is not None:
        df1 = df1[df1["NS venue name"] == venue1]
    if year1 is not None:
        df1 = df1[df1["AA year of publication"] == year1]

    if venue2 is not None and year2 is not None:
        df2 = get_dataset(False)
        if venue2 is not None:
            df2 = df2[df2["NS venue name"] == venue2]
        if year2 is not None:
            df2 = df2[df2["AA year of publication"] == year2]
        count_.count_compare_words(k, df1, df2)
    else:
        count_.count_compare_words(k, df1)


@cli.command()
def test():
    from nlpland.data_cleanup import clean_and_tokenize
    test_ = "one two, three.\n four-five, se-\nven, open-\nsource, se-\nve.n, "

    # clean_and_tokenize(test_, get_vocabulary())


if __name__ == '__main__':
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(extract, ["anth", "--original"])
    # traceback.print_exception(*result.exc_info)
