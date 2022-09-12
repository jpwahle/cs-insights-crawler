"""This module implements continous retrieval of DBLP releases, crawling of PDFs, extraction of
metadata, and storing to the backend
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Union

import appdirs
import click

from csinsights.client import SemanticScholarClient
from csinsights.data.s2processor import SemanticScholarDataProcessor
from csinsights.log import set_glob_logger
from csinsights.types import AccessType

default_cache_dir = None
try:
    default_cache_dir = Path(appdirs.user_cache_dir(__name__, os.getlogin()))
except:  # noqa: E722
    default_cache_dir = None


def filter_options(function: Callable) -> Callable:
    """Combine multiple CLI filter options in one annotation.

    Args:
        function (Callable): The original function that we extend.

    Returns:
        Expanded function for the annotation.
    """
    # General options
    function = click.option(
        "--verbose", is_flag=True, help="Whether to print a lot or not. Default is False."
    )(function)
    function = click.option(
        "--cache_dir",
        is_flag=False,
        type=str,
        default=default_cache_dir,
        help="Where to cache downloads. Default is ~/.cache/csinsights.",
    )(function)

    # DBLP options
    function = click.option(
        "--dblp_base_url",
        is_flag=False,
        type=str,
        default="https://dblp.org/xml",
        help="The base url of the DBLP release page. Default is https://dblp.org/xml.",
    )(function)
    function = click.option(
        "--dblp_access_type",
        is_flag=False,
        type=set,
        default={AccessType.OPEN},
        help="Filters DBLP with the specified access type (OPEN, CLOSED, ALL). Default is OPEN.",
    )(function)
    function = click.option(
        "--dblp_use_filters",
        is_flag=True,
        help="Whether to use the filters above. Default is False.",
    )(function)

    # S2 options
    function = click.option(
        "--s2_base_url",
        is_flag=False,
        type=str,
        default="https://api.semanticscholar.org/datasets/v1/",
        help=(
            "The base url of the SemanticScholar release page. Default is"
            " https://api.semanticscholar.org/datasets/v1/ ."
        ),
    )(function)
    function = click.option(
        "--s2_use_papers",
        is_flag=True,
        help="The core attributes of a paper (title, authors, date, etc.).",
    )(function)
    function = click.option(
        "--s2_use_abstracts",
        is_flag=True,
        help="Whether to download abstracts. Default is False.",
    )(function)
    function = click.option(
        "--s2_use_authors",
        is_flag=True,
        help="Whether to download author information. Default is False.",
    )(function)
    function = click.option(
        "--s2_use_citations",
        is_flag=True,
        help="Whether to download citation information. Default is False.",
    )(function)
    function = click.option(
        "--s2_use_embeddings",
        is_flag=True,
        help="Whether to download embeddings for full texts. Default is False.",
    )(function)
    function = click.option(
        "--s2_use_s2orc",
        is_flag=True,
        help="Whether to download full-texts. Default is False.",
    )(function)
    function = click.option(
        "--s2_use_tldrs",
        is_flag=True,
        help="Whether to download too long; didn't reads for full texts. Default is False.",
    )(function)
    function = click.option(
        "--s2_filter_acl",
        is_flag=True,
        help=(
            "Whether to filter everything out except the ACL Anthology. Works also in combination"
            " with other filters as union. Default is False."
        ),
    )(function)
    function = click.option(
        "--s2_filter_dblp",
        is_flag=True,
        help=(
            "Whether to filter everything out except DBLP. Works also in combination"
            " with other filters as union. Default is False."
        ),
    )(function)
    function = click.option(
        "--s2_filter_pubmed",
        is_flag=True,
        help=(
            "Whether to filter everything out except PubMed. Works also in combination"
            " with other filters as union. Default is False."
        ),
    )(function)
    function = click.option(
        "--s2_filter_pubmedcentral",
        is_flag=True,
        help=(
            "Whether to filter everything out except PubMed. Works also in combination"
            " with other filters as union. Default is False."
        ),
    )(function)
    function = click.option(
        "--s2_filter_arxiv",
        is_flag=True,
        help=(
            "Whether to filter everything out except arXiv. Works also in combination"
            " with other filters as union. Default is False."
        ),
    )(function)

    return function


def main(**kwargs: Union[str, int, bool, datetime, AccessType]) -> None:
    """The main process of continous crawling, processing, and storing to our backend API.

    Args:
        **kwargs: Dict arguments for the process comming from command-line args in `filter_options`.
    """
    # If verbose is set, print all debug messages
    if kwargs["verbose"]:
        assert isinstance(kwargs["verbose"], bool)
        set_glob_logger(**kwargs)  # type: ignore
    # Create SemanticScholar client with api key from env
    api_key = os.environ.pop("S2_API_KEY", None)
    assert (
        api_key is not None
    ), "Please set the S2_API_KEY environment variable if you want to use SemanticScholar."
    # Get cache_dir
    cache_dir = Path(str(kwargs.pop("cache_dir")))
    # Create client
    s2client = SemanticScholarClient(cache_dir=cache_dir, api_key=api_key, **kwargs)  # type: ignore
    # Get latest timestamp of backend and update
    release_version = s2client.download_release(api_key=api_key, **kwargs)  # type: ignore
    # Create SemanticScholar data processor
    s2processor = SemanticScholarDataProcessor(cache_dir=cache_dir, **kwargs)  # type: ignore
    # Process data
    dataset = s2processor.process_data(cache_dir=cache_dir, **kwargs)  # type: ignore
    # Store data
    dataset.to_jsonl(f"~/d3-releases/{release_version}/")
    dataset.to_csv(f"~/d3-releases/{release_version}")
    # Clean cache
    s2processor.clean_cache()
