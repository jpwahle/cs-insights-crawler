"""This module implements continous retrieval of DBLP releases, crawling of PDFs, extraction of
metadata, and storing to the backend
"""
import multiprocessing
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Union

import appdirs
import click
from scrapy.crawler import CrawlerProcess  # type: ignore

from csinsights.client import DBLPClient, transform_dataset_to_scrapy
from csinsights.crawler.spiders.dblp import DblpSpider
from csinsights.log import set_glob_logger
from csinsights.types import AccessType


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

    # DBLP options
    function = click.option(
        "--dblp_base_url", is_flag=False, type=str, default="https://dblp.org/xml"
    )(function)
    function = click.option(
        "--dblp_access_type", is_flag=False, type=set, default={AccessType.OPEN}
    )(function)
    function = click.option("--dblp_use_filters", is_flag=True)(function)

    # Grobid options
    function = click.option(
        "--grobid_service",
        is_flag=False,
        type=str,
        default="processHeaderDocument",
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


def main(**kwargs: Union[str, int, bool, datetime, AccessType]) -> None:
    """The main process of continous crawling, processing, and storing to our backend API.

    Args:
        **kwargs: Dict arguments for the process comming from command-line args in `filter_options`.
    """
    # Create scrapy crawler process
    process = CrawlerProcess()
    # If verbose is set, print all debug messages
    if kwargs["verbose"]:
        assert isinstance(kwargs["verbose"], bool)
        set_glob_logger(**kwargs)  # type: ignore
    # Get props from CLI
    dblp_base_url = str(kwargs.pop("dblp_base_url"))
    # Get user_cache_dir and init clients, processor, and crawler
    cache_dir = Path(appdirs.user_cache_dir(__name__, os.getlogin()))
    dblp_client = DBLPClient(cache_dir=cache_dir, base_url=dblp_base_url)
    # Get latest timestamp of backend and update **kwargs
    dataset_dict = dblp_client.download_and_filter_release(**kwargs)  # type: ignore
    # Transform large dataset dict to small lists for crawling in scraoy
    dblp_keys, strat_urls = transform_dataset_to_scrapy(dataset_dict, **kwargs)  # type: ignore
    # Crawl PDFs
    process.crawl(DblpSpider, cache_dir=cache_dir, dblp_keys=dblp_keys, start_urls=strat_urls)
    process.start()
