import click

import nlpland.dataset as data
import nlpland.data_cleanup as clean
from dotenv import load_dotenv

load_dotenv()


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
    if original:
        df = data.load_dataset("PATH_DATASET")
    else:
        df = data.load_dataset("PATH_DATASET_EXPANDED")

    modes = ["rule", "anth"]
    if mode not in modes:
        print(f"Unsupported mode '{mode}'. Choose from {modes}.")
    if mode == "rule":
        data.extract_abstracts_rulebased(df, overwrite_abstracts=overwrite, min_year=min_year, max_year=max_year)
    elif mode == "anth":
        data.extract_abstracts_anthology(df)


@cli.command()
@click.option('--original', is_flag=True)
def extractanth(original):
    if original:
        df = data.load_dataset("PATH_DATASET")
    else:
        df = data.load_dataset("PATH_DATASET_EXPANDED")
    data.extract_abstracts_anthology(df)


if __name__ == '__main__':
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(extract, ["anth", "--original"])
    #traceback.print_exception(*result.exc_info)