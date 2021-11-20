"""This module implements a client to communicate with DBLP."""
import gzip
import hashlib
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Callable, Iterator, List, Set, Tuple, TypeVar

import requests
from bs4 import BeautifulSoup
from lxml import etree
from tqdm import tqdm  # type: ignore

from nlpland.log.logger import LogMixin
from nlpland.types import AccessType, Url

# region helpers


def local_md5(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        return md5_in_chunks(f)


def remote_md5(file_url: Url) -> str:
    md5_url = file_url + ".md5"
    page = requests.get(md5_url).text
    md5 = page.partition(" ")[0]
    return md5


def md5_in_chunks(file: BinaryIO, block_size: int = 2 ** 20) -> str:
    md5 = hashlib.md5()
    while True:
        data = file.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def download_in_chunks(url: str, file_path: Path, chunk_size: int = 1024) -> None:
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))

    progress_bar = tqdm(unit="B", total=total_size_in_bytes)
    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                progress_bar.update(len(chunk))
                file.write(chunk)


def compare_md5(md5_1: str, md5_2: str) -> bool:
    return md5_1 == md5_2


def filter_by_timestamp_fn(
    children: List[etree._Element], from_timestamp: datetime
) -> Iterator[etree._Element]:
    return filter(
        lambda x: datetime.strptime(str(x.attrib.get("mdate")), "%Y-%m-%d") > from_timestamp,
        children,
    )


def filter_by_access_fn(
    children: List[etree._Element], access_types: Set[AccessType]
) -> Iterator[etree._Element]:
    def _filter(element: etree._Element) -> bool:
        children_of_element = element.iterchildren()
        for child in children_of_element:
            if child.tag == "ee":
                return any(
                    [
                        access_type.value in child.attrib.get("type", "")  # type: ignore
                        for access_type in access_types
                    ]
                )
        return False

    return filter(_filter, children)


def create_timestamp_filter(
    from_timestamp: datetime,
) -> Callable[[List[etree._Element]], List[etree._Element]]:
    return lambda x: list(filter_by_timestamp_fn(x, from_timestamp))


def create_open_access_filter(
    access_types: Set[AccessType],
) -> Callable[[List[etree._Element]], List[etree._Element]]:
    return lambda x: list(filter_by_access_fn(x, access_types))


# endregion

T = TypeVar("T", bound="DBLPClient")


class DBLPClient(LogMixin):
    def __init__(
        self: T,
        cache_dir: Path,
        base_url: Url,
        filename_suffixes: Tuple[str, str, str] = (".md5", ".gz", ".dtd"),
    ) -> None:
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.filename_suffixes = filename_suffixes
        self.releases = []

    @property
    def cache_dir(self: T) -> Path:
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self: T, new_cache_dir: Path) -> None:
        os.makedirs(new_cache_dir, exist_ok=True)
        self._cache_dir = new_cache_dir

    @property
    def releases(self: T) -> List[Url]:
        """Getter of the release urls

        Returns:
            List[Url]: The release_urls
        """
        if not self._releases:
            self.releases = self._fetch_releases()
        return self._releases

    @releases.setter
    def releases(self: T, new_releases: List[Url]) -> None:
        """Setter of the release urls

        Args:
            new_releases (List[Url]): The new release urls
        """
        self._releases = new_releases

    def download_and_filter_release(
        self: T, from_timestamp: datetime, **kwargs: Any
    ) -> List[etree._Element]:

        # time the opertaion for debugging purposes
        start = time.perf_counter()

        # download latest xml, dtd, and check md5 hash
        file_path_xml = self._download_and_extract_latest_xml()

        # create filters (strongest filters first for performance reasons)
        timestmap_filter = create_timestamp_filter(from_timestamp)
        # TODO: Make access type an argument
        access_filter = create_open_access_filter({AccessType.OPEN})
        filters = [timestmap_filter, access_filter]

        # load xml in memory with validated dtd schema and filter by timestamp
        filtered_children = self._load_and_filter_xml(file_path_xml, *filters)

        end = time.perf_counter()

        self.logger.debug(
            "Downloaded and filtered xml (function download_and_filter_release)"
            f" {end - start:.2f} seconds"
        )

        # Return filtered children
        return filtered_children

    def _load_and_filter_xml(
        self: T,
        file_path_xml: Path,
        *filters: Callable[[List[etree._Element]], List[etree._Element]],
    ) -> List[etree._Element]:
        # load xml file into memory and get children
        tree = self.load_xml_and_get_children(file_path_xml)

        # filter xml according to `filters`
        filtered_children = self._filter_xml(tree, *filters)

        return filtered_children

    def _filter_xml(
        self: T,
        children: List[etree._Element],
        *filters: Callable[[List[etree._Element]], List[etree._Element]],
    ) -> List[etree._Element]:
        self.logger.debug(f"Filtering elements according to `filters`. {self.long_opertaion_log}")

        res = children
        for filter in filters:
            res = filter(res)

        return res

    def _fetch_releases(self: T, desc: bool = True) -> List[str]:
        url = f"{self.base_url}/release"
        page = requests.get(url).text
        soup = BeautifulSoup(page, "html.parser")
        file_list = [
            url + "/" + node.get("href")
            for node in soup.find_all("a")
            if node.get("href").endswith(self.filename_suffixes)
        ]
        file_list.sort(reverse=desc)

        return file_list

    def _get_latest_release_file(self: T, extension: str, n: int = 1) -> str:
        iterator = (url for url in self.releases if url.endswith(extension))
        latest_url = ""
        for _ in range(n):
            latest_url = next(iterator)
        return latest_url

    def _download_and_extract_latest_xml(self: T) -> Path:

        self._download_latest_dtd()
        xml_gz_url = self._get_latest_release_file(extension=".xml.gz")
        file_path_gz = self._download_xml(xml_gz_url)
        file_path_xml = self._unzip_xml_gz(file_path_gz)

        return file_path_xml

    def _download_latest_dtd(self: T) -> None:
        dtd_url = self._get_latest_release_file(extension=".dtd")
        self._download_dtd(dtd_url)

    def _download_dtd(self: T, dtd_url: Url) -> None:
        # If cached file is already there, skip
        dtd_name = dtd_url.rpartition("/")[-1]
        file_path = Path(os.path.join(self.cache_dir, dtd_name))
        if os.path.isfile(file_path):
            self.logger.debug(f"Using cached {file_path}")
        else:
            file_path = Path(os.path.join(self.cache_dir, dtd_name))
            download_in_chunks(dtd_url, file_path)
            self.logger.debug(f"Saved file {file_path}")

    def _download_xml(self: T, file_url: Url) -> Path:
        file_name = file_url.rpartition("/")[-1]
        file_path = Path(os.path.join(self.cache_dir, file_name))
        md5_remote = remote_md5(file_url)
        # If cached file is already there and has correct md5, skip
        if os.path.isfile(file_path) and compare_md5(local_md5(file_path), md5_remote):
            self.logger.debug(f"Using cached {file_path}")
        else:
            # Download the dataset
            download_in_chunks(file_url, file_path)
            self.logger.debug(f"Saved file {file_path}")
            if not compare_md5(local_md5(file_path), md5_remote):
                raise ValueError("Md5 of downloaded file does not match with remote md5")
        return file_path

    def _unzip_xml_gz(self: T, file_path_in: Path) -> Path:
        # Unzip the dataset if zipped
        if file_path_in.suffix == ".gz":
            # Remove .gz suffix
            file_path_out = file_path_in.with_suffix("")
            # if the xml already exists, skip
            if os.path.isfile(file_path_out):
                self.logger.debug(f"Using cached {file_path_out}")
                return file_path_out

            self.logger.debug(f"Unzipping {file_path_in} to {file_path_out}")
            # Always unzip. Only then it is guranteed that the md5 was matched
            # Otherwise when the process is canceled we can not guarantee the file is not corrupted
            with gzip.open(file_path_in, "rb") as f_in, open(file_path_out, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            self.logger.debug(f"Saved file {file_path_out}")
            return file_path_out
        raise FileNotFoundError("File extension is not .gz")

    def load_xml_and_get_children(self: T, file_path_xml: Path) -> List[etree._Element]:
        # load main tree
        tree = self._load_xml(file_path_xml)
        # retrieve first-level children
        return self._get_children(tree)

    def _load_xml(self: T, file_path_xml: Path) -> etree._ElementTree:

        # Convert path to string because of lxml type annotation
        path = str(file_path_xml)

        # dtd needs to be in the same directory as the xml
        self.logger.debug(f"Parsing xml file {file_path_xml} {self.long_opertaion_log}")
        parser = etree.XMLParser(dtd_validation=True)
        return etree.parse(path, parser=parser)

    def _get_children(self: T, tree: etree._ElementTree) -> List[etree._Element]:
        # get first-level children from main tree
        self.logger.debug("Getting first-level children")
        return list(tree.getroot().iterchildren())
