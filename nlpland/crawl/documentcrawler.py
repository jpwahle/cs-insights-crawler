"""This module implements the asynchronous retrieval of abstracts either from the publication's
webpage or, if not available, from pdfs.
"""
import asyncio
import multiprocessing
import os
import random
import shutil
import urllib.parse
from pathlib import Path
from typing import Any, Callable, List, Optional, Type, TypeVar
from urllib.parse import urljoin

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from bs4.element import ResultSet

from nlpland.log.logger import LogMixin
from nlpland.types import Url


def arxiv_matcher(soup: BeautifulSoup) -> ResultSet:
    return soup.select("a[href*='/pdf/']")


def general_matcher(soup: BeautifulSoup) -> ResultSet:
    return soup.select("a[href$='.pdf']")


def choose_matcher(url: Url) -> Callable[[BeautifulSoup], ResultSet]:
    if "arxiv" in url:
        return arxiv_matcher
    else:
        return general_matcher


V = TypeVar("V")


def chunk_list(lst: List[V], n: int) -> List[List[V]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]  # noqa: E203


T = TypeVar("T", bound="DocumentCrawler")


class DocumentCrawler(LogMixin):
    def __init__(
        self: T,
        cache_dir: Path,
        pub_urls: List[Url],
        pub_keys: List[str],
        chunk_size: int,
        overwrite_pdf_cache_dir: bool = False,
        **kwargs: Any,
    ) -> None:

        assert len(pub_urls) == len(pub_keys), "pub_urls and pub_keys must have the same length"

        self.cache_dir = cache_dir
        self.pub_urls = pub_urls
        self.pub_keys = pub_keys
        self.chunk_size = chunk_size
        self.overwrite_pdf_cache_dir = overwrite_pdf_cache_dir
        self.pdf_cache_dir = Path(os.path.join(cache_dir, "pdf"))

    @property
    def cache_dir(self: T) -> Path:
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self: T, new_cache_dir: Path) -> None:
        os.makedirs(new_cache_dir, exist_ok=True)
        self._cache_dir = new_cache_dir

    @property
    def pdf_cache_dir(self: T) -> Path:
        return self._pdf_cache_dir

    @pdf_cache_dir.setter
    def pdf_cache_dir(self: T, new_cache_dir: Path) -> None:
        if os.path.exists(new_cache_dir) and os.path.isdir(new_cache_dir):
            if not self.overwrite_pdf_cache_dir:
                self.logger.error(
                    f"{new_cache_dir} already exists to cache PDF files. Please use"
                    " overwrite_pdf_cache_dir to overwrite"
                )
                raise FileExistsError(f"{new_cache_dir} already exists")
            else:
                shutil.rmtree(new_cache_dir)
        os.makedirs(new_cache_dir, exist_ok=True)
        if self.chunk_size:
            for i in range(1, len(self.pub_urls) // self.chunk_size + 1):
                dir = os.path.join(new_cache_dir, f"chunk{i:08d}")
                os.makedirs(dir, exist_ok=True)
        self._pdf_cache_dir = new_cache_dir

    @property
    def num_chunks(self: T) -> int:
        return len(os.listdir(self.pdf_cache_dir))

    def sync_run_main_until_complete(self: T) -> None:

        # Init variables
        manager = multiprocessing.Manager()
        return_list = manager.list()
        pdf_processes = []

        # Get chunked lists of pub_urls and pub_keys
        chunked_pub_urls: List[List[Url]] = list(chunk_list(self.pub_urls, self.chunk_size))
        chunked_pub_keys: List[List[Url]] = list(chunk_list(self.pub_keys, self.chunk_size))

        # Create a process for the first chunk and start it
        previous_request_process = multiprocessing.Process(
            target=self.sync_run_requests,
            args=(chunked_pub_urls[0], chunked_pub_keys[0], 0, return_list),
        )
        previous_request_process.start()

        # Iterate over all remaining chunks
        for chunk, (pub_urls_current, pub_keys_current) in enumerate(
            zip(chunked_pub_urls, chunked_pub_keys), 1  # skip chunk 0 because it already started
        ):
            # Create process for current chunk
            current_request_process = multiprocessing.Process(
                target=self.sync_run_requests,
                args=(pub_urls_current, pub_keys_current, chunk, return_list),
            )
            # Create process for working on the previous chunk
            process_process_pdf = multiprocessing.Process(
                target=self.process_pdfs, args=(chunk - 1,)  # safely subtract 1 as we start with 1
            )
            # Add pdf process to list to join later
            pdf_processes.append(process_process_pdf)
            # Start the next process to crawl in the background
            current_request_process.start()
            # Wait for the previous process to finish so we can work on chunk's data
            previous_request_process.join()
            # Set the previous process to be the next process to crawl
            previous_request_process = current_request_process
            # Work on the data that the previous process crawled while the current process crawls the current chunk
            process_process_pdf.start()

        current_request_process.join()

        for pdf_process in pdf_processes:
            pdf_process.join()

        print(return_list)

    def process_pdfs(self: T, chunk: int) -> None:
        dir = os.path.join(self.cache_dir, "pdf", f"chunk{chunk:08d}")
        print(os.listdir(dir))

    def sync_run_requests(
        self: T, pub_urls: List[Url], pub_keys: List[str], chunk: int, return_list: List[str]
    ) -> None:

        filenames_for_chunk = asyncio.run(self.async_run_requests(pub_urls, pub_keys, chunk))
        for el in filenames_for_chunk:
            return_list.append(el)

    async def async_run_requests(
        self: T, pub_urls: List[Url], pub_keys: List[str], chunk: int
    ) -> List[str]:
        tasks = []
        async with aiohttp.ClientSession() as session:
            for url, key in zip(pub_urls, pub_keys):
                tasks.append(
                    asyncio.ensure_future(
                        self.async_get_abstract(session=session, url=url, key=key, chunk=chunk)
                    )
                )
            filenames = await asyncio.gather(*tasks)
            return filenames

    async def async_get_abstract(
        self: T, session: aiohttp.ClientSession, url: Url, key: str, chunk: int
    ) -> Optional[str]:
        async with session.get(url) as resp:
            if resp.status == 200:
                # Success: Download pdf and store according to the unique key
                content = await resp.text()
                soup = BeautifulSoup(content, "html.parser")
                matcher = choose_matcher(url)

                for link in matcher(soup):
                    dir = os.path.join(self.cache_dir, "pdf", f"chunk{chunk:08d}")
                    os.makedirs(dir, exist_ok=True)
                    filepath = os.path.join(dir, f"{key}.pdf")

                    async with aiofiles.open(filepath, "wb") as f:
                        base_url = urllib.parse.urlparse(url).netloc
                        pdf_url = urljoin(f"https://{base_url}", link["href"])  # type: ignore
                        async with session.get(str(pdf_url)) as pdf:
                            self.logger.debug(f"Downloading {pdf_url} to {filepath}")
                            await f.write(await pdf.read())
                            return filepath
            else:
                # Unsuccessful: Wait up to a second and try again.
                return await self.async_get_abstract(session, url, key, chunk)

        return None


if __name__ == "__main__":

    import appdirs

    cache_dir = Path(appdirs.user_cache_dir("nlp-land-crawler", os.getlogin()))
    document_crawler = DocumentCrawler(
        cache_dir=cache_dir,
        pub_urls=[
            "https://arxiv.org/abs/2111.07819",
            "https://arxiv.org/abs/2106.07967",
            "https://arxiv.org/abs/2103.12450",
            "https://arxiv.org/abs/2103.11909",
        ]
        * 10,
        pub_keys=["2111.07819", "2106.07967", "2103.12450", "2103.11909"] * 10,
        chunk_size=4,
        overwrite_pdf_cache_dir=True,
    )
    document_crawler.sync_run_main_until_complete()
