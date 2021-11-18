from datetime import datetime
import gzip
import hashlib
from io import BufferedReader
import os
import shutil
from typing import Optional, List, Union

import requests
from bs4 import BeautifulSoup
from lxml import etree
from tqdm import tqdm

from nlpland.log.logger import LogMixin

# region helpers


def local_md5(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return md5_in_chunks(f)


def remote_md5(file_url: str) -> str:
    md5_url = file_url + ".md5"
    page = requests.get(md5_url).text
    md5 = page.partition(" ")[0]
    return md5


def md5_in_chunks(file: BufferedReader, block_size=2 ** 20):
    md5 = hashlib.md5()
    while True:
        data = file.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def download_in_chunks(url: str, file_path: str, chunk_size: int = 1024) -> None:
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


# endregion


class DBLPClient(LogMixin):
    def __init__(
        self,
        cache_dir: str,
        base_url="https://dblp.org/xml",
        filename_suffixes=("md5", "gz", "dtd"),
    ) -> None:
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.filename_suffixes = filename_suffixes
        self.releases = []

    @property
    def cache_dir(self) -> str:
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, new_cache_dir: str) -> None:
        os.makedirs(new_cache_dir, exist_ok=True)
        self._cache_dir = new_cache_dir

    @property
    def releases(self) -> List[str]:
        if not self._releases:
            self.releases = self.fetch_releases()
        return self._releases

    @releases.setter
    def releases(self, new_releases: List[str]) -> None:
        self._releases = new_releases

    def download_and_filter_release(self, from_timestamp: Union[str, int, datetime.date]) -> None:
        # TODO implement
        # 1. fetch latest release
        # 2. Filter XML for all files that have not been touched after `from_timestamp`
        # 3. Return a dataset with all entities in a geberic format

        # download latest dtd
        dtd_url = self.get_latest_release_file(extension=".dtd")
        file_path_dtd = self.download_dtd(dtd_url)

        # download latest xml.gz
        xml_gz_url = self.get_latest_release_file(extension=".xml.gz")
        file_path_gz = self.download_xml(xml_gz_url)
        file_path_xml = self.unzip_xml_gz(file_path_gz)

        # TODO: load xml in memory and validate against dtd schema
        xml = self.load_xml(file_path_xml)

        # TODO: filter xml according to `from_timestamp`

        # TODO: return an instance of a XMLDataset

    def fetch_releases(self, desc: bool = True) -> List[str]:
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

    def get_latest_release_file(self, extension: str, n: int = 1) -> str:
        iterator = (url for url in self.releases if url.endswith(extension))
        latest_url = ""
        for _ in range(n):
            latest_url = next(iterator)
            print(latest_url)
        return latest_url

    def download_dtd(self, dtd_url: str) -> str:
        # If cached file is already there, skip
        dtd_name = dtd_url.rpartition("/")[-1]
        file_path = os.path.join(self.cache_dir, dtd_name)
        if os.path.isfile(file_path):
            self.logger.info(f"No .dtd downloaded, file already exists at {file_path}.")
        else:
            file_path = os.path.join(self.cache_dir, dtd_name)
            download_in_chunks(dtd_url, file_path)
            self.logger.info(f"Saved file {file_path}")

        return file_path

    def download_xml(self, file_url: str) -> Optional[str]:
        file_name = file_url.rpartition("/")[-1]
        file_path = os.path.join(self.cache_dir, file_name)
        md5_remote = remote_md5(file_url)
        # If cached file is already there and has correct md5, skip
        if os.path.isfile(file_path) and compare_md5(local_md5(file_path), md5_remote):
            self.logger.info("No .xml.gz downloaded, file already exists and md5 matches.")
        else:
            # Download the dataset
            download_in_chunks(file_url, file_path)
            self.logger.info(f"Saved file {file_path}")
            if not compare_md5(local_md5(file_path), md5_remote):
                self.logger.info("MD5 of downloaded file does not match.")
        return file_path

    def unzip_xml_gz(self, file_path_in: str) -> str:

        # Unzip the dataset if zipped
        self.logger.info("Unzipping file...")
        if file_path_in.endswith(".gz"):
            file_path_out = file_path_in[:-3]
            # Always unzip. Only then it is guranteed that the md5 was matched
            # Otherwise when the process is canceled we can not guarantee the file is not corrupted
            with gzip.open(file_path_in, "rb") as f_in, open(file_path_out, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            self.logger.info(f"Saved file {file_path_out}")
            return file_path_out

    def load_xml(self, file_path_xml: str) -> Optional[etree.XML]:
        # dtd needs to be in the same directory as the xml
        parser = etree.XMLParser(dtd_validation=True)
        return etree.parse(file_path_xml, parser=parser)
