"""This module implements continous retrieval of DBLP releases, crawling of PDFs, extraction of
metadata, and storing to the Nlp-Land-backend
"""
import multiprocessing
import os
from pathlib import Path
from typing import Any, Callable

import appdirs
import click

from nlpland.client import BackendClient, DBLPClient, GrobidClient
from nlpland.crawl import DocumentCrawler
from nlpland.data import Dataset
from nlpland.log import set_glob_logger
from nlpland.types import AccessType, ValidGrobidServices


def filter_options(function: Callable) -> Callable:
    """Combine multiple CLI filter options in one annotation.

    Args:
        function (Callable): The original function that we extend.

    Returns:
        Expanded function for the annotation.
    """
    # General options
    function = click.option("--verbose", is_flag=True)(function)
    function = click.option("--store_local", is_flag=True)(function)

    # Backend options
    function = click.option(
        "--backend_base_url", is_flag=False, type=str, default="http://localhost:3000"
    )(function)

    # DBLP options
    function = click.option(
        "--dblp_base_url", is_flag=False, type=str, default="https://dblp.org/xml"
    )(function)
    function = click.option(
        "--dblp_access_type", is_flag=False, type=set, default={AccessType.OPEN}
    )(function)
    function = click.option("--dblp_use_filters", is_flag=True)(function)

    # Crawler options
    function = click.option("--crawler_chunk_size", is_flag=False, type=int, default=1000)(function)
    function = click.option("--crawler_overwrite_pdf_cache_dir", is_flag=True)(function)
    function = click.option("--crawler_shuffle_requests", is_flag=True, default=True)(function)
    function = click.option("--crawler_max_concurrent_requests", is_flag=False, default=50)(
        function
    )

    # Grobid options
    function = click.option(
        "--grobid_service",
        is_flag=False,
        type=ValidGrobidServices,
        default=ValidGrobidServices.processHeaderDocument,
    )(function)
    function = click.option("--grobid_server", is_flag=False, type=str, default="http://localhost")(
        function
    )
    function = click.option("--grobid_port", is_flag=False, type=int, default=8070)(function)
    function = click.option(
        "--grobid_pdf_extraction_threads",
        is_flag=False,
        type=int,
        default=multiprocessing.cpu_count(),
    )(function)
    function = click.option("--grobid_batch_size", is_flag=False, type=int, default=100)(function)
    function = click.option("--grobid_generate_ids", is_flag=True)(function)
    function = click.option("--grobid_consolidate_header", is_flag=True)(function)
    function = click.option("--grobid_consolidate_citations", is_flag=True)(function)
    function = click.option("--grobid_include_raw_citations", is_flag=True)(function)
    function = click.option("--grobid_include_raw_affiliations", is_flag=True)(function)
    function = click.option("--grobid_tei_coordinates", is_flag=True)(function)
    function = click.option("--grobid_segment_sentences", is_flag=True)(function)

    return function


def main(**kwargs: Any) -> None:
    """The main process of continous crawling, processing, and storing to our backend API.

    Args:
        **kwargs: Dict arguments for the process comming from command-line args in `filter_options`.
    """
    # If verbose is set, print all debug messages
    if kwargs["verbose"]:
        set_glob_logger(**kwargs)
    # Get props from CLI
    dblp_base_url = kwargs.pop("dblp_base_url")
    backend_base_url = kwargs.pop("backend_base_url")
    # Get user_cache_dir and init clients, processor, and crawler
    cache_dir = Path(appdirs.user_cache_dir(__name__, os.getlogin()))
    dblp_client = DBLPClient(cache_dir=cache_dir, base_url=dblp_base_url)
    backend_client = BackendClient(base_url=backend_base_url)
    grobid_client = GrobidClient(**kwargs)
    # Get latest timestamp of backend and update **kwargs
    latest_timestamps = backend_client.get_latest_timestamps(**kwargs)
    kwargs.update({"dblp_from_timestamp": latest_timestamps})
    # Download and filter release according to timestamp
    dataset_dict = dblp_client.download_and_filter_release(**kwargs)
    # Get the publication's urls and unique keys from the dataset
    pub_urls, pub_keys = Dataset.extract_urls_and_keys(dataset_dict=dataset_dict)
    # Extract abstracts and other useful metadata with grobid
    document_crawler = DocumentCrawler(
        cache_dir=cache_dir,
        pdf_extraction_fn=grobid_client.process,
        pub_urls=pub_urls,
        pub_keys=pub_keys,
        **kwargs,
    )
    extraced_meta = document_crawler.crawl_documents_and_extract_meta(**kwargs)
    # Encode Entities in backend (json/dict) format
    dataset = Dataset.convert_to_schema(dataset_dict=dataset_dict)
    # Add crawled documents to dataset
    dataset = dataset.add(to_add=extraced_meta)
    if kwargs.get("store_local"):
        # Cache dataset to disk
        dataset.store_local(path=cache_dir)
    # TODO: GET, POST, PATCH entities in backend
    backend_client.store(dataset)
