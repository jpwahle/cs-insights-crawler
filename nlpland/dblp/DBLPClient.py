# export
import datetime
import gzip
import hashlib
import os
import shutil
from typing import Tuple, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class DBLPClient:
    def __init__(self, base_url: str, cache_dir: str, filename_prefix: str,
                 filename_suffixes: Tuple[str]) -> None:
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.filename_prefix = filename_prefix
        self.filename_suffixes = filename_suffixes

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, new_base_url: str):
        # if not validators.url(new_base_url):
        #     raise ValueError(f"{new_base_url} is not a valid url")
        self._base_url = new_base_url

    @property
    def cache_dir(self):
        return self._base_url

    @cache_dir.setter
    def cache_dir(self, new_cache_dir: str):
        os.makedirs(new_cache_dir, exist_ok=True)
        self._cache_dir = new_cache_dir

    def check_md5(self, filepath: str, md5: str) -> bool:
        return self.md5(filepath) == md5

    def md5(self, filepath: str):
        return hashlib.md5(open(filepath, "rb").read()).hexdigest()

    def get_request_handle(
            self, url: str, stream: bool = False, chunk_size: Optional[int] = None
    ):
        if stream:
            return requests.get(url, stream=stream).iter_content(chunk_size=chunk_size)
        return requests.get(url)

    def download_latest_dtd(self, date: datetime) -> str:

        releases = self.fetch_releases()

        # Find out which is the most recent dtd

        dtd = self.download_dtd(self.cache_dir, date)
        return dtd

    def download_dtd(self, cache_dir: str, date: datetime):
        # If cached file is already there, skip
        if os.path.isfile(os.path.join(cache_dir, "dblp.dtd")):
            return

        # Download the dataset
        file_path = os.path.join(cache_dir, "dblp.dtd")
        request_handle = self.get_request_handle(f"{self.base_url}/dblp.dtd")
        with open(file_path, "wb") as f:
            for chunk in tqdm(request_handle):
                if chunk:
                    f.write(chunk)

        return file_path

    def download_xml(self, cache_dir: str, file_name: str, old_md5: str) -> Optional[str]:
        file_path = os.path.join(cache_dir, file_name)
        # If cached file is already there and has correct md5, skip
        if os.path.isfile(file_path) and self.check_md5(file_path, old_md5):
            return

        # Download the dataset
        request_handle = self.get_request_handle(
            f"{self.base_url}/{file_name}", stream=True, chunk_size=1024
        )
        with open(file_path, "wb") as f:
            for chunk in tqdm(request_handle):
                if chunk:
                    f.write(chunk)

        # Unzip the dataset if zipped
        if file_name.endswith(".gz"):
            with gzip.open(file_path, "rb") as f_in, open(
                    file_path[:-3], "wb"
            ) as f_out:
                shutil.copyfileobj(f_in, f_out)

        return file_path

    def fetch_releases(self, order="desc"):
        url = f"{self.base_url}/release"
        page = self.get_request_handle(url).text
        soup = BeautifulSoup(page, 'html.parser')
        filelist = [url + '/' + node.get('href') for node in soup.find_all('a') if
                    node.get('href').endswith(self.filename_suffixes)]
        filelist.sort(reverse=order == 'desc')

        return filelist

    def download_paper(self):
        pass

    def get_author_by_id(self):
        pass

    def get_venue_by_id(self):
        pass

    def get_paper_by_id(self):
        pass
