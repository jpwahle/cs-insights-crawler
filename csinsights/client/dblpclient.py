"""This module implements a client to communicate with DBLP."""
import gzip
import hashlib
import json
import os
import shutil
import time
from datetime import datetime
from gzip import GzipFile
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Set, Tuple, TypeVar, Union

import requests
import xmltodict  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from lxml import etree

# Check if types are available soon https://github.com/tqdm/tqdm/issues/260
from tqdm import tqdm  # type: ignore

from csinsights.log import LogMixin
from csinsights.types import AccessType, DatasetJsonDict, FilterFunction, Url

# region helpers


def local_md5(filepath: Path) -> str:
    """Calculate the MD5 hash of a file.

    Args:
        filepath (Path): The file to compute the hash for.

    Returns:
        str: The MD5 hash of the file in hex format.
    """
    with open(filepath, "rb") as f:
        return md5_in_chunks(f)


def remote_md5(file_url: Url) -> str:
    """Retrieve the MD5 hash of a remote file.

    Args:
        file_url (Url): The url of a remote md5 file.

    Returns:
        str: The MD5 hash of the remote file in hex format.
    """
    md5_url = file_url + ".md5"
    page = requests.get(md5_url).text
    md5 = page.partition(" ")[0]
    return md5


def md5_in_chunks(file: BinaryIO, block_size: int = 2 ** 20) -> str:  # noqa: BLK100
    """Calculate the MD5 hash of a file iteratively in chunks.

    Args:
        file (BinaryIO): The file to compute the hash for.
        block_size (int, optional): The chunk block size in bytes. Defaults to 2**20.

    Returns:
        str: The md5 hash of the file in hex format.
    """
    md5 = hashlib.md5()
    while True:
        data = file.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def download_in_chunks(url: str, file_path: Path, chunk_size: int = 1024) -> None:
    """Download a file in chunks.

    Args:
        url (str): The url of the file to download.
        file_path (Path): The path to the file to download to.
        chunk_size (int, optional): The chunk size in bytes. Defaults to 1024.
    """
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))

    progress_bar = tqdm(unit="B", total=total_size_in_bytes)
    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                progress_bar.update(len(chunk))
                file.write(chunk)


def compare_md5(md5_1: str, md5_2: str) -> bool:
    """Compares two MD5 hashes.

    Args:
        md5_1 (str): First MD5 hash in hex format.
        md5_2 (str): Second MD5 hash in hex format.

    Returns:
        bool: Returns whether the MD5 hashes are equal.
    """
    return md5_1 == md5_2


def filter_by_timestamp_fn(tree: DatasetJsonDict, from_timestamp: datetime) -> DatasetJsonDict:
    """A filter function to filter out all elements that have not been modified
    before a given timestamp.

    Args:
        tree (DatasetJsonDict): The tree to filter.
        from_timestamp (datetime): The timestamp to filter by.

    Returns:
        DatasetJsonDict: The filtered tree.
    """
    filtered = {
        element_list_key: [
            el
            for el in element_list
            if datetime.strptime(str(el.get("@mdate")), "%Y-%m-%d") > from_timestamp
        ]
        for element_list_key, element_list in tree.items()
    }
    return filtered


def filter_by_access_fn(tree: DatasetJsonDict, access_types: Set[AccessType]) -> DatasetJsonDict:
    """A filter function to filter out all elements that are no having a certain access type

    Args:
        tree (DatasetJsonDict): The tree to filter.
        access_types (Set[AccessType]): A set of valid access types. All other access types will be
        filtered out.

    Returns:
        DatasetJsonDict: The filtered tree.
    """
    filtered = {
        element_list_key: [
            el
            for el in element_list
            if el.get("ee", {"@type": AccessType.CLOSED}).get("@type") in access_types
        ]
        for element_list_key, element_list in tree.items()
    }
    return filtered


def create_timestamp_filter(
    from_timestamp: datetime,
) -> FilterFunction:
    """A helper function that transforms the filter iterator to a list.

    Args:
        from_timestamp (datetime): The timestamp to filter by.

    Returns:
        FilterFunction: A function to be called that returns a filtered of elements.
    """
    return lambda x: filter_by_timestamp_fn(x, from_timestamp)


def create_open_access_filter(
    access_types: Set[AccessType],
) -> FilterFunction:
    """A helper function that transforms the filter iterator to a list.

    Args:
        access_types (Set[AccessType]): The access types to filter by.

    Returns:
        FilterFunction: A function to be called that returns a filtered elements.
    """
    return lambda x: filter_by_access_fn(x, access_types)


# endregion

T = TypeVar("T", bound="DBLPClient")


class DBLPClient(LogMixin):
    """A client for the DBLP XML releases.

    Args:
        LogMixin (Any): A shared log mixin class.
    """

    def __init__(
        self: T,
        cache_dir: Path,
        base_url: Url,
        filename_suffixes: Tuple[str, str, str] = (".md5", ".gz", ".dtd"),
    ) -> None:
        """Constructor the the DBLPClient

        Args:
            self (T): This object.
            cache_dir (Path): The cache directory to store releases in.
            base_url (Url): The base url of the DBLP release page.
            filename_suffixes (Tuple[str, str, str], optional): Suffixes for release files.
            Defaults to (".md5", ".gz", ".dtd").
        """
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.filename_suffixes = filename_suffixes
        self.releases = []

    @property
    def cache_dir(self: T) -> Path:
        """Getter for the cache directory to store releases in.

        Args:
            self (T): This object.

        Returns:
            Path: Path to the current cache directory.
        """
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self: T, new_cache_dir: Path) -> None:
        """Setter for the cache directory to store releases in.
        Creates the cache directory if it doesn't exist.

        Args:
            self (T): This object.
            new_cache_dir (Path): The new cache directory.
        """
        os.makedirs(new_cache_dir, exist_ok=True)
        self._cache_dir = new_cache_dir

    @property
    def releases(self: T) -> List[Url]:
        """Getter of the release urls.

        Returns:
            List[Url]: The release_urls
        """
        if not self._releases:
            self.releases = self._fetch_releases()
        return self._releases

    @releases.setter
    def releases(self: T, new_releases: List[Url]) -> None:
        """Setter of the release urls.

        Args:
            new_releases (List[Url]): The new release urls.
        """
        self._releases = new_releases

    def download_and_filter_release(
        self: T,
        dblp_use_filters: bool,
        dblp_access_type: Set[AccessType],
        dblp_from_timestamp: datetime = datetime(1980, 1, 1),
        **kwargs: Union[str, int, bool, AccessType, datetime],
    ) -> DatasetJsonDict:
        """Downloads and filters the latest release according to the given parameters.

        Args:
            self (T): This object.
            from_timestamp (datetime): Filter parameter. Ignore all objects which have been
            modified before.
            dblp_access_type (AccessType, optional): [description]. Filter parameter. Ignore all
            objects which are not having the given access type. Defaults to AccessType.OPEN.

        Returns:
            DatasetJsonDict: Returns a tree of elements from the release after filtering.
        """
        # time the opertaion for debugging purposes
        start = time.perf_counter()
        # Get serialized cache file if it exists
        serialized_path = self._get_serialized_cache_hit()
        # If there is a cache hit for the current release, load it from there and skip other steps
        if serialized_path:
            # Load the serialized file
            tree = self._deserialize_tree(file_path=serialized_path)
        # Otherwise download the latest release, compare md5 hashes, extract, and serialize it
        else:
            # download latest xml, dtd, and check md5 hash
            file_path_xml_gz = self._download_latest_xml()
            # load main tree
            tree = self._load_xml_as_dict(file_path_xml_gz)
            # serialize the tree to a file
            self._serialize_tree(tree)
        # Init filters
        filters = []
        # Use filters only if flag is set
        if dblp_use_filters:
            # create filters (strongest filters first for performance reasons)
            timestmap_filter = create_timestamp_filter(dblp_from_timestamp)
            if dblp_access_type is not AccessType.ALL:
                access_filter = create_open_access_filter(dblp_access_type)
            filters.extend([timestmap_filter, access_filter])
        # filter release according to `filters`
        filtered_tree = self._filter_elements(tree, *filters)
        # time the operation for debugging purposes
        end = time.perf_counter()
        # in debug mode, log the time it took to download and filter the xml
        self.logger.debug(
            f"Downloaded and filtered release {'with' if serialized_path else 'without'} cache"
            f" in {end - start:.2f} seconds."
        )
        # Return filtered children
        return filtered_tree

    def _get_filename_from_url(self: T, url: Url) -> Path:
        """Get the filename from the url.

        Args:
            url (Url): The url to get the filename from.

        Returns:
            Path: The filename from the url.
        """
        return Path(os.path.join(self.cache_dir, url.rpartition("/")[-1]))

    def _deserialize_tree(self: T, file_path: Path) -> DatasetJsonDict:
        self.logger.debug(
            f"Deserializing tree from file {str(file_path)} {self.long_opertaion_log}"
        )
        # Open filepath and read json (this can take up to three minutes)
        with open(file_path, "r") as f:
            tree: DatasetJsonDict = json.load(f)
            return tree

    def _serialize_tree(self: T, tree: DatasetJsonDict) -> None:
        # Get the latest release url
        xml_gz_url = self._get_latest_release_file(extension=".xml.gz")
        # get the serialized path
        serialized_path = self._get_filename_from_url(url=xml_gz_url).with_suffix(".json")
        self.logger.debug(
            f"Serializing tree to file {str(serialized_path)} {self.long_opertaion_log}"
        )
        # serialize the tree to a file
        with open(serialized_path, "w") as f:
            json.dump(tree, f)

    def _get_serialized_cache_hit(self: T) -> Optional[Path]:
        # Get the latest release url
        xml_gz_url = self._get_latest_release_file(extension=".xml.gz")
        # Get the serialized cache path
        serialized_path = self._get_filename_from_url(url=xml_gz_url).with_suffix(".json")
        # Check if there exists a serialized cache hit for the current release
        if serialized_path.exists() and serialized_path.is_file():
            # If there is a cache hit, load it from there and skip other steps
            return serialized_path
        # If there is no cache hit, return None
        return None

    def _filter_elements(
        self: T,
        tree: DatasetJsonDict,
        *filters: FilterFunction,
        **kwargs: Dict[str, Any],
    ) -> DatasetJsonDict:
        """Filtering elements from a JSON dict.

        Args:
            self (T): This object.
            children (DatasetJsonDict): Elements to filter.

        Returns:
            DatasetJsonDict: A filtered JSON dict.
        """
        # Get the arg whether to filter or not
        dblp_use_filters = kwargs.pop("dblp_use_filters", True)
        # Set the results to the input children
        res = tree
        # Check whether to filter or not. The filters would not have been created if the flag is
        # not set but this is a safe check.
        if dblp_use_filters:
            # In debug mode, log the operation
            self.logger.debug(
                f"Filtering elements according to `filters` {self.long_opertaion_log}"
            )
            # Apply filters sequentially
            for filter_ in filters:
                res = filter_(res)
        # Return filtered children
        return res

    def _fetch_releases(self: T, desc: bool = True) -> List[str]:
        # Get release url
        url = f"{self.base_url}/release"
        page = requests.get(url).text
        # Parse the page
        soup = BeautifulSoup(page, "html.parser")
        # Filter all hyperlinks (these are the release links)
        file_link_list = [
            url + "/" + node.get("href")
            for node in soup.find_all("a")
            if node.get("href").endswith(self.filename_suffixes)
        ]
        # Sort list according to name which results in accoring to date
        file_link_list.sort(reverse=desc)
        # Return list of release links
        return file_link_list

    def _get_latest_release_file(self: T, extension: str, skip: int = 1) -> str:
        # get iterator over all releases ordered by date
        iterator = (url for url in self.releases if url.endswith(extension))
        latest_url = ""
        # get the latest release according to `skip`
        for _ in range(skip):
            latest_url = next(iterator)
        # return the latest release url
        return latest_url

    def _download_latest_xml(self: T) -> Path:
        # get latest dtd file
        self._download_latest_dtd()
        # get latest xml file
        xml_gz_url = self._get_latest_release_file(extension=".xml.gz")
        # download xml file
        file_path_gz = self._download_xml(xml_gz_url)
        # return xml file path
        return file_path_gz

    def _download_latest_dtd(self: T) -> None:
        # Download the latest dtd file
        dtd_url = self._get_latest_release_file(extension=".dtd")
        self._download_dtd(dtd_url)

    def _download_dtd(self: T, dtd_url: Url) -> None:
        # Get filename and path
        file_path = self._get_filename_from_url(url=dtd_url)
        # If dtd is already there, skip
        if os.path.isfile(file_path):
            self.logger.debug(f"Using cached {file_path}")
        # If not, download it
        else:
            download_in_chunks(dtd_url, file_path)
            self.logger.debug(f"Saved file {file_path}")

    def _download_xml(self: T, file_url: Url) -> Path:
        # Get filename, path, and remote md5 hash
        file_path = self._get_filename_from_url(url=file_url)
        md5_remote = remote_md5(file_url)
        # If cached file is already there and has correct md5, skip
        if os.path.isfile(file_path) and compare_md5(local_md5(file_path), md5_remote):
            self.logger.debug(f"Using cached {file_path}")
        # Else, download the dataset
        else:
            download_in_chunks(file_url, file_path)
            self.logger.debug(f"Saved file {file_path}")
            if not compare_md5(local_md5(file_path), md5_remote):
                # If the md5 doesn't match, raise an error
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

    def _load_xml(self: T, file_path_xml: Path) -> etree._ElementTree:
        # Convert path to string because of lxml `parse` function type annotation
        path = str(file_path_xml)
        self.logger.debug(f"Parsing xml file {file_path_xml} {self.long_opertaion_log}")
        # Parse xml with dtd schema
        parser = etree.XMLParser(dtd_validation=True)
        # dtd needs to be in the same directory as the xml
        return etree.parse(path, parser=parser)

    def _load_xml_as_dict(self: T, file_path_gz: Path) -> DatasetJsonDict:
        self.logger.debug(
            f"Loading {file_path_gz} in streaming mode as dict {self.long_opertaion_log}"
        )
        # This operation is very slow. However, it only has to be executed once per release
        # (i.e., once per month). After that everything is cached to JSON.
        parsed_dict: Dict[str, DatasetJsonDict] = xmltodict.parse(GzipFile(file_path_gz))
        return parsed_dict["dblp"]
