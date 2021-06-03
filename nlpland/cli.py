import click

import nlpland.dataset as data
import nlpland.data_cleanup as clean


@click.command()
def cli():
    """Parse a timezone and greet a location a number of times."""
    print("hi")


@click.command()
def download():
    click.echo('Initialized the database')


@click.command()
@click.option('--original', is_flag=True)
@click.option('--overwrite', is_flag=True)
@click.option('--min-year')
@click.option('--max-year')
def extractrule(original, overwrite, min_year=None, max_year=None):
    if original:
        df = data.load_dataset("PATH_DATASET")
    else:
        df = data.load_dataset("PATH_DATASET_EXPANDED")
    data.extract_abstracts_rulebased(df, overwrite_abstracts=overwrite)


@click.command()
@click.option('--original', is_flag=True)
def extractanth(original):
    if original:
        df = data.load_dataset("PATH_DATASET")
    else:
        df = data.load_dataset("PATH_DATASET_EXPANDED")
    data.extract_abstracts_anthology(df)

