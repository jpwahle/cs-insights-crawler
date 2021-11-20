"""This module implements continous retrieval of DBLP releases, crawling of PDFs, extraction of
metadata, and storing to the Nlp-Land-backend
"""
import os
from pathlib import Path
from typing import Any, Callable

import appdirs
import click

from nlpland.client import DBLPClient  # type: ignore
from nlpland.client import BackendClient, backend_schemas
from nlpland.crawl.documentcrawler import DocumentCrawler
from nlpland.transform.transform import Transformer  # type: ignore


def filter_options(function: Callable) -> Callable:
    """Combine multiple CLI filter options in one annotation.

    Args:
        function (Callable): The original function that we extend.

    Returns:
        Expanded function for the annotation.
    """
    function = click.option("--use_venues", is_flag=True)(function)
    function = click.option("--use_authors", is_flag=True)(function)
    function = click.option("--use_publications", is_flag=True)(function)
    function = click.option("--use_affiliations", is_flag=True)(function)

    function = click.option("--overwrite_pdf_cache_dir", is_flag=True)(function)

    function = click.option(
        "--backend_base_url", is_flag=False, type=str, default="http://localhost:3000"
    )(function)
    function = click.option(
        "--dblp_base_url", is_flag=False, type=str, default="https://dblp.org/xml"
    )(function)
    return function


def main(**kwargs: Any) -> None:
    """The main process of continous crawling, processing, and storing to backend API.

    Args:
        **kwargs: Dict arguments for the process comming from command-line args in `filter_options`.
    """
    dblp_base_url = kwargs.pop("dblp_base_url")
    backend_base_url = kwargs.pop("backend_base_url")

    # Get user_cache_dir and init clients, processor, and crawler
    cache_dir = Path(appdirs.user_cache_dir("nlp-land-crawler", os.getlogin()))
    dblp_client = DBLPClient(cache_dir=cache_dir, base_url=dblp_base_url)
    backend_client = BackendClient(cache_dir=cache_dir, base_url=backend_base_url)

    # Get latest timestamp of backend and update **kwargs
    latest_timestamps = backend_client.get_latest_timestamps(**kwargs)
    kwargs.update({"from_timestamp": latest_timestamps})

    # Download and filter release according to timestamp
    dataset = dblp_client.download_and_filter_release(**kwargs)

    # TODO: Encode Entities in backend (json/dict) format
    dataset_dict = Transformer.convert_to_schema(
        entities=dataset,
        author_schema=backend_schemas.Author,
        affiliation_schema=backend_schemas.Affiliation,
        publication_schema=backend_schemas.Publication,
        venue_schema=backend_schemas.Venue,
    )

    # TODO: Extract abstracts and other useful metadata

    document_crawler = DocumentCrawler(cache_dir, [], [], chunk_size=1000, **kwargs)
    pdf_paths = document_crawler.retrieve_pdfs(dataset_dict)
    json_dataset_with_abstracts = document_crawler.extract_meta(json_dataset, pdf_paths)

    # TODO: GET, POST, PATCH, DELETE entities in backend
    backend_client.run_queries(json_dataset_with_abstracts)
