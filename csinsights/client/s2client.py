"""This module implements a client to communicate with SemanticScholar (S2)."""
import os
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TypeVar, Union

import requests  # type: ignore
from tqdm import tqdm

from csinsights.log import LogMixin
from csinsights.types import AccessType, Url

# region helpers


unsupported_features = [
    "s2_use_citations",
    "s2_use_embeddings",
    "s2_use_tldrs",
]


def download_in_chunks(
    url: str, file_path: Path, chunk_size: int = 1024 ** 2  # noqa: BLK100
) -> None:
    """Download a file in chunks.

    Args:
        url (str): The url of the file to download.
        file_path (Path): The path to the file to download to.
        chunk_size (int, optional): The chunk size in bytes. Defaults to 1024 ** 2.
    """
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))

    progress_bar = tqdm(
        unit="MB",
        total=int(total_size_in_bytes / chunk_size),
    )  # type: ignore
    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                progress_bar.update()
                file.write(chunk)
    response.close()


# endregion

T = TypeVar("T", bound="SemanticScholarClient")


class SemanticScholarClient(LogMixin):
    """A client for the SemanticScholarClient releases.

    Args:
        LogMixin (Any): A shared log mixin class.
    """

    def __init__(
        self: T,
        cache_dir: Path,
        s2_base_url: Url,
        api_key: Optional[str] = None,
        **kwargs: Union[str, int, bool, AccessType, datetime],
    ) -> None:
        """Constructor the the SemanticScholarClient

        Args:
            self (T): This object.
            cache_dir (Path): The cache directory to store releases in.
            s2_base_url (Url): The base url of the DBLP release page.
            api_key (Optional[str], optional): The API key to use. Defaults to None.
        """
        self.base_url = s2_base_url
        self.cache_dir = cache_dir
        self.headers = {"x-api-key": api_key} if api_key else None

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

    def download_release(
        self: T,
        **kwargs: Union[str, int, bool, AccessType, datetime],
    ) -> str:
        """Downloads the latest release of the SemanticScholar bulk dataset api.

        Args:
            self (T): This object.

        Raises:
            NotImplementedError: If the release is not supported yet.

        Returns:
            str: The current (and downloaded) release version.
        """
        # Store file paths for later processing
        file_paths = []
        # Check if any of the not supported features are used
        if any([kwargs[feature] for feature in unsupported_features]):
            raise NotImplementedError(
                f"The following features are not supported yet: {unsupported_features}"
            )
        # Time the opertaion for debugging purposes
        start = time.perf_counter()
        # Get latest release version
        release_version = self._fetch_lastest_release_version()
        # Get release url
        target_url = urllib.parse.urljoin(self.base_url, f"release/{release_version}/")
        # Get data for all features
        for arg in kwargs:
            if arg.startswith("s2_use_") and kwargs[arg]:
                file_paths.extend(self._fetch_releases(target_url, arg.split("_")[-1]))

        # Get the time it took to download the data
        end = time.perf_counter()
        # in debug mode, log the time it took to download and filter the xml
        self.logger.debug(f"Downloaded release in {end - start:.2f} seconds.")
        self.logger.info(f"Done fetching {len(file_paths)} files from release {release_version}.")
        # Return release version
        return release_version

    def _fetch_releases(self: T, release_url: str, dataset: str) -> List[Path]:
        # Store file_paths for later processing
        file_paths = []
        # Get target url
        target_url = urllib.parse.urljoin(release_url, f"dataset/{dataset}/")
        # Get all files
        res = requests.get(target_url, headers=self.headers)
        for index, download_link in enumerate(res.json()["files"]):
            path = Path(os.path.join(self.cache_dir, f"{dataset}_{index}.jsonl.gz"))
            download_in_chunks(download_link, path)
            file_paths.append(path)
        return file_paths

    def _fetch_lastest_release_version(self: T) -> str:
        # Get release url
        target_url = urllib.parse.urljoin(self.base_url, "release/")
        releases: List[str] = list(requests.get(target_url, headers=self.headers).json())
        # Sort list according to name which results in accoring to date
        releases.sort(reverse=True)
        # Select the latest release from the last month. This is guaranteed to have all metadata
        # The most recent release might not have all metadata yet.
        latest_prefix = "-".join(releases[0].split("-")[:1])  # What is the latest (e.g., 2020-10)
        # Get a list of everything from before the latest release
        filtered_releases = [
            release for release in releases if not release.startswith(latest_prefix)
        ]
        # Get the latest release from before the latest release
        return filtered_releases[0]
