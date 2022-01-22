"""This module implements the asynchronous retrieval of abstracts either from the publication's
webpage or, if not available, from pdfs.
"""
import asyncio
import multiprocessing
import os
import shutil
import time
from tqdm import tqdm
import urllib.parse
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, TypeVar
from urllib.parse import urljoin

import aiofiles  # type: ignore
import aiohttp
import git
from bs4 import BeautifulSoup
from bs4.element import ResultSet
import random

from nlpland.data import Dataset
from nlpland.log import LogMixin, set_glob_logger
from nlpland.types import PdfExtractionFn, Url

# region: Helper functions


def delete_files_with_type_from_folder(type: str, folder: Path) -> None:
    """Delete all files with the given type from the given folder.

    Args:
        type (str): The type of files to delete.
        folder (Path): The folder to delete the files from.
    """
    for file in folder.glob(f"*{type}"):
        file.unlink()


def check_extract_pdf_processes(
    pdf_processes_and_args: List[Tuple[multiprocessing.Process, Dict[str, Any]]],
    timeout: Optional[float] = None,
) -> None:
    for process, kwargs in pdf_processes_and_args:
        process.join(timeout=timeout)
        if process.is_alive():
            # Job is not finished yet
            continue
        else:
            # Job is finished, so remove pdfs because of storage requirements
            delete_files_with_type_from_folder(".pdf", Path(kwargs["input_path"]))
            # Remove the pdf process from the list
            pdf_processes_and_args.remove((process, kwargs))


def arxiv_pdf_matcher(soup: BeautifulSoup) -> ResultSet:
    """A matcher for arxiv.org.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to search in.

    Returns:
        ResultSet: A result set of found pdfs
    """
    return soup.select("a[href*='/pdf/']")


def general_pdf_matcher(soup: BeautifulSoup) -> ResultSet:
    """The fallback matcher for any website.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to search in.

    Returns:
        ResultSet: A result set of found pdfs
    """
    return soup.select("a[href$='.pdf']")


def choose_matcher(url: Url) -> Callable[[BeautifulSoup], ResultSet]:
    """Returns a matcher function based on the url.

    Args:
        url (Url): The Url to match against.

    Returns:
        Callable[[BeautifulSoup], ResultSet]:  A function to find the pdfs using BeautifulSoup.
    """
    if "arxiv" in url:
        return arxiv_pdf_matcher
    else:
        return general_pdf_matcher


V = TypeVar("V")


def shuffle_lists(list_a: List[V], list_b: List[V]) -> Tuple[List[V], List[V]]:
    tmp = list(zip(list_a, list_b))
    random.shuffle(tmp)
    res_a, res_b = zip(*tmp)
    return res_a, res_b  # type: ignore


def chunk_list(lst: List[V], n: int) -> Generator[List[V], None, None]:
    """Chunk a list with n chunks.

    Args:
        lst (List[V]): The list to chunk in n chunks.
        n (int): The number of chunks.

    Yields:
        Generator[List[V], None, None]: The chunks of the list as a Generator.
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]  # noqa: E203


# endregion

T = TypeVar("T", bound="DocumentCrawler")


class DocumentCrawler(LogMixin):

    _cache_dir: Path
    _pdf_cache_dir: Path
    _git_hash: str

    def __init__(
        self: T,
        cache_dir: Path,
        pub_urls: List[Url],
        pub_keys: List[str],
        crawler_chunk_size: int,
        pdf_extraction_fn: PdfExtractionFn,
        crawler_overwrite_pdf_cache_dir: bool = False,
        crawler_shuffle_requests: bool = True,
        crawler_max_concurrent_requests: int = 100,
        **kwargs: Any,
    ) -> None:
        # Check if the lists are of equal length
        assert len(pub_urls) == len(pub_keys), "pub_urls and pub_keys must have the same length"

        if crawler_shuffle_requests:
            pub_urls, pub_keys = shuffle_lists(pub_urls, pub_keys)

        self.cache_dir = cache_dir
        self.pub_urls = pub_urls
        self.pub_keys = pub_keys
        self.chunk_size = crawler_chunk_size
        self.overwrite_pdf_cache_dir = crawler_overwrite_pdf_cache_dir
        self.max_concurrent_requests = crawler_max_concurrent_requests
        self.pdf_extraction_fn = pdf_extraction_fn
        self.pdf_cache_dir = Path(os.path.join(cache_dir, "pdf"))

        repo = git.Repo()
        self._git_hash = repo.head.object.hexsha

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
        # If the pdf_cache_dir is not empty, we need to make sure that we don't overwrite the pdfs
        if os.path.exists(new_cache_dir) and os.path.isdir(new_cache_dir):
            # If the user explicitly wants to overwrite the pdf cache dir, we can do that
            if not self.overwrite_pdf_cache_dir:
                self.logger.error(
                    f"{new_cache_dir} already exists to cache PDF files. Please use"
                    " overwrite_pdf_cache_dir to overwrite"
                )
                raise FileExistsError(f"{new_cache_dir} already exists")
            else:
                shutil.rmtree(new_cache_dir)
        # Create pdf cache dir if it doesn't exist
        os.makedirs(new_cache_dir, exist_ok=True)
        # Create chunk dirs
        if self.chunk_size:
            for i in range(1, len(self.pub_urls) // self.chunk_size + 1):
                dir = os.path.join(new_cache_dir, f"chunk{i:08d}")
                os.makedirs(dir, exist_ok=True)
        # Set the pdf cache dir
        self._pdf_cache_dir = new_cache_dir

    @property
    def num_chunks(self: T) -> int:
        # Get the number of chunks according to the created chunk dirs
        return len(os.listdir(self.pdf_cache_dir))

    def crawl_documents_and_extract_meta(self: T, **kwargs: Any) -> Dataset:
        filepaths = self._crawl(**kwargs)
        return self._extract(filepaths, **kwargs)

    def _crawl(self: T, **kwargs: Any) -> List[str]:
        # Init list
        return_path_list: List[str] = []
        # Get chunked lists of pub_urls and pub_keys
        chunked_pub_urls: List[List[Url]] = list(chunk_list(self.pub_urls, self.chunk_size))
        chunked_pub_keys: List[List[str]] = list(chunk_list(self.pub_keys, self.chunk_size))
        # Iterate over all remaining chunks
        for chunk, (pub_urls_current, pub_keys_current) in tqdm(
            enumerate(
                zip(chunked_pub_urls, chunked_pub_keys),
                1,  # skip chunk 0 because it already started
            )
        ):
            # Create process for current chunk
            self._sync_run_requests(pub_urls_current, pub_keys_current, chunk, return_path_list)
        return return_path_list

    def _crawl_the_real_deal(self: T, **kwargs: Any) -> List[str]:
        # Init variables
        manager = multiprocessing.Manager()
        return_path_list: List[str] = manager.list()
        pdf_processes_and_args: List[Tuple[multiprocessing.Process, Dict[str, Any]]] = []
        # Get chunked lists of pub_urls and pub_keys
        chunked_pub_urls: List[List[Url]] = list(chunk_list(self.pub_urls, self.chunk_size))
        chunked_pub_keys: List[List[str]] = list(chunk_list(self.pub_keys, self.chunk_size))
        # Create a process for the first chunk and start it
        previous_request_process = multiprocessing.Process(
            target=self._sync_run_requests,
            args=(chunked_pub_urls[0], chunked_pub_keys[0], 0, return_path_list),
        )
        previous_request_process.start()
        # Iterate over all remaining chunks
        for chunk, (pub_urls_current, pub_keys_current) in enumerate(
            zip(chunked_pub_urls, chunked_pub_keys), 1  # skip chunk 0 because it already started
        ):
            # Create process for current chunk
            current_request_process = multiprocessing.Process(
                target=self._sync_run_requests,
                args=(pub_urls_current, pub_keys_current, chunk, return_path_list),
            )
            # Get path of current chunk and update as kwarg
            chunk_path = Path(
                os.path.join(self.cache_dir, "pdf", f"chunk{chunk-1:08d}")
            )  # safely subtract 1 as we start with 1
            kwargs.update({"input_path": chunk_path})
            # Create process for working on the previous chunk
            extract_pdf_process = multiprocessing.Process(
                target=self.pdf_extraction_fn, kwargs=kwargs
            )
            # Add pdf process and kwargs to list to check later
            pdf_processes_and_args.append((extract_pdf_process, kwargs))
            # Start the next process to crawl in the background
            current_request_process.start()
            # Wait for the previous process to finish so we can work on chunk's data
            previous_request_process.join()
            # Set the previous process to be the next process to crawl
            previous_request_process = current_request_process
            # Work on the data that the previous process crawled while new data is fetched
            extract_pdf_process.start()
            # Check extract_pdf_processes for finished. If so, remove the pdfs.
            check_extract_pdf_processes(pdf_processes_and_args, timeout=0.0)
        # Join the previous process to make sure that we have finished crawling all chunks
        previous_request_process.join()
        # Wait for last request process to finish
        current_request_process.join()
        # For all processes that have not been finished in the main loop, join them and remove pdfs
        check_extract_pdf_processes(pdf_processes_and_args, timeout=None)
        # Return all pdf paths
        return return_path_list

    def _extract(self: T, filepaths: List[str], **kwargs: Any) -> Dataset:
        # Get extracted metadata from files and return
        return_dict = {}
        for item in filepaths:
            # Get extracted meta from pdf
            extracted_meta_path = Path(item).with_suffix(".tei.xml")
            # Convert to dict
            with open(extracted_meta_path, "r") as f:
                # Prase with BeautifulSoup
                soup = BeautifulSoup(f, "lxml")
                # Get main entites
                authors = soup.find_all("author")
                title = soup.find("title").getText()
                abstract = soup.find("abstract").getText()

                # For all authors get their affiliations
                for author in authors:
                    affiliations = author.find_all("affiliation")

                    for affiliation in affiliations:

                        organisation_name = affiliation.find("orgname").getText()
                        addressline = affiliation.find("addrline").getText()
                        postcode = (
                            affiliation.find("postcode").getText()
                            if affiliation.find("postcode")
                            else None
                        )
                        city = (
                            author.find("settlement").getText()
                            if author.find("settlement")
                            else None
                        )
                        country = (
                            author.find("country").getText() if author.find("country") else None
                        )
                        countrycode = (
                            author.find("country").get("key") if author.find("country") else None
                        )

        return Dataset(return_dict)

    def _sync_run_requests(
        self: T, pub_urls: List[Url], pub_keys: List[str], chunk: int, return_list: List[str]
    ) -> None:
        # Run all requests in each chunk asynchronously to mitigate IO overhead
        filenames_for_chunk = asyncio.run(self._async_run_requests(pub_urls, pub_keys, chunk))
        # Add filenames to shared return list
        for el in filenames_for_chunk:
            return_list.append(el)

    async def _async_run_requests(
        self: T, pub_urls: List[Url], pub_keys: List[str], chunk: int
    ) -> List[str]:
        # Create a list to store the tasks for returning the pdfs
        tasks = []
        # Limit the number of concurrent requests to avoid being banned
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        # Create a new aiohttp session
        async with aiohttp.ClientSession(trust_env=True) as session:
            # Create a new async task for each entry in the list
            for url, key in zip(pub_urls, pub_keys):
                tasks.append(
                    asyncio.ensure_future(
                        self._async_find_pdf(
                            session=session, semaphore=semaphore, url=url, key=key, chunk=chunk
                        )
                    )
                )
            # Join all tasks in asyncio.gather returning the file names of each async_get_pdf call
            filenames = await asyncio.gather(*tasks)
            return filenames

    async def _store_pdf(self: T, filepath: Path, pdf: Any) -> None:
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(pdf)

    async def _async_find_pdf(
        self: T,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        url: Url,
        key: str,
        chunk: int,
    ) -> Optional[str]:
        # Limit number of concurrent requests to avoid being banned
        async with semaphore:
            try:
                # Get abstract from the url
                async with session.get(url, ssl=False) as resp:
                    if resp.status == 200:
                        # Assign filepath according to chunk and key
                        chunk_path = os.path.join(self.cache_dir, "pdf", f"chunk{chunk:08d}")
                        os.makedirs(chunk_path, exist_ok=True)
                        # Keys might contain slashes "/" which are not allowed in file names
                        file_key = key.replace("/", "-")
                        filepath = os.path.join(chunk_path, f"{file_key}.pdf")
                        # If the url already points to a pdf, store if (no double downloads)
                        if resp.headers.get("content-type") == "application/pdf":
                            # If the url is directly pointing to the pdf, get it directly from the resp
                            pdf = await resp.read()
                            asyncio.sleep(0)
                            self.logger.debug(f"Downloading {url} to {filepath}")
                            await self._store_pdf(Path(filepath), pdf)
                        else:
                            # Otherwise find the pdf form the html page
                            content = await resp.text()
                            # Match pdf url from the html page
                            soup = BeautifulSoup(content, "html.parser")
                            matcher = choose_matcher(url)
                            # TODO: We don't want all pdfs. Implement a heuristic for the correct pdf.
                            for link in matcher(soup):
                                # Download and store pdf
                                base_url = urllib.parse.urlparse(url).netloc
                                pdf_url = urljoin(f"https://{base_url}", link["href"])  # type: ignore
                                async with session.get(str(pdf_url), ssl=False) as pdf_resp:
                                    self.logger.debug(f"Downloading {pdf_url} to {filepath}")
                                    await self._store_pdf(Path(filepath), await pdf_resp.read())
                                    return filepath

                    elif resp.status == 429:
                        # If we made too many requests, we might get a retry-after header to wait for
                        asyncio.sleep(int(resp.headers["Retry-After"]))
                        return await self._async_find_pdf(session, semaphore, url, key, chunk)
            except aiohttp.client_exceptions.ClientConnectionError:
                self.logger.debug(msg=f"Skipping {url} becuase of connection error.")
            return None


if __name__ == "__main__":

    # TODO: Use the code below for writing unit tests.
    import appdirs
    from nlpland.client import GrobidClient

    set_glob_logger(verbose=True)

    client = GrobidClient(
        grobid_server="http://localhost",
        grobid_port=8070,
        grobid_batch_size=100,
    )

    cache_dir = Path(appdirs.user_cache_dir("nlp-land-crawler", os.getlogin()))
    document_crawler = DocumentCrawler(
        cache_dir=cache_dir,
        crawler_chunk_size=4,
        pub_urls=[
            "https://export.arxiv.org/abs/2111.07819",
            "https://export.arxiv.org/abs/2106.07967",
            "https://export.arxiv.org/abs/2103.12450",
            "https://export.arxiv.org/abs/2103.11909",
        ]
        * 3,
        pub_keys=["2111.07819", "2106.07967", "2103.12450", "2103.11909"] * 3,
        crawler_overwrite_pdf_cache_dir=True,
        pdf_extraction_fn=client.process,
    )
    document_crawler.crawl_documents_and_extract_meta()
