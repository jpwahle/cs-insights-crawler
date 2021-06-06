import click

import nlpland.dataset as data
import nlpland.data_cleanup as clean
import nlpland.data_check as check
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
    df = data.load_dataset("PATH_DATASET")
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
    df = data.load_dataset("PATH_DATASET_EXPANDED")
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


if __name__ == '__main__':
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(extract, ["anth", "--original"])
    #traceback.print_exception(*result.exc_info)
