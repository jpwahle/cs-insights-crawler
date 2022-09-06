from typing import Any, List

import scrapy  # noqa

from csinsights.grobid2json.process_pdf import process_pdf_file


class DblpSpider(scrapy.Spider):

    name = "dblp"

    def __init__(self, cache_dir: str, start_urls: List[str], dblp_keys: List[str]):
        self.cache_dir = cache_dir
        self.start_urls = start_urls
        self.dblp_keys = dblp_keys

    def parse(self, response: Any) -> None:
        results_path = process_pdf_file(response)
