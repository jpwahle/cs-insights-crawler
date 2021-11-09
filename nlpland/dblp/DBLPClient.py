import gzip
import hashlib
import os
import shutil
from typing import Optional, List

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class DBLPClient:
    def __init__(self, cache_dir: str) -> None:
        self.base_url = "https://dblp.org/xml"
        self.cache_dir = cache_dir
        self.filename_suffixes = ("md5", "gz", "dtd")
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

    def fetch_releases(self, desc: bool = True) -> List[str]:
        url = f"{self.base_url}/release"
        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html.parser')
        file_list = [url + '/' + node.get('href') for node in soup.find_all('a') if
                     node.get('href').endswith(self.filename_suffixes)]
        file_list.sort(reverse=desc)

        return file_list

    def latest_url_for_extension(self, extension: str) -> str:
        latest_url = next(url for url in self.releases if url.endswith(extension))
        return latest_url

    def check_md5(self, filepath: str, md5: str) -> bool:
        return self.local_md5(filepath) == md5

    def local_md5(self, filepath: str) -> str:
        return hashlib.md5(open(filepath, "rb").read()).hexdigest()

    def remote_md5(self) -> str:
        md5_url = self.latest_url_for_extension(".md5")
        page = requests.get(md5_url).text
        md5 = page.partition(" ")[0]
        return md5

    def download_in_chunks(self, url: str, file_path: str, chunk_size: int = 1024) -> None:
        response = requests.get(url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))

        progress_bar = tqdm(unit="B", total=total_size_in_bytes)
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    progress_bar.update(len(chunk))
                    file.write(chunk)

    def download_dtd(self, dtd_url: str) -> str:
        # If cached file is already there, skip
        dtd_name = dtd_url.rpartition("/")[-1]
        file_path = os.path.join(self.cache_dir, dtd_name)
        if os.path.isfile(file_path):
            print("No .dtd downloaded, file already exists.")
        else:
            file_path = os.path.join(self.cache_dir, dtd_name)
            self.download_in_chunks(dtd_url, file_path)
            print(f"Saved file {file_path}")

        return file_path

    def download_xml(self, file_url: str) -> Optional[str]:
        file_name = file_url.rpartition("/")[-1]
        file_path = os.path.join(self.cache_dir, file_name)
        md5 = self.remote_md5()
        # If cached file is already there and has correct md5, skip
        if os.path.isfile(file_path) and self.check_md5(file_path, md5):
            print("No .xml.gz downloaded, file already exists and md5 matches.")
        else:
            # Download the dataset
            self.download_in_chunks(file_url, file_path)
            print(f"Saved file {file_path}")
            if not self.check_md5(file_path, md5):
                print("Hash of downloaded file does not match. Please try again.")
        return file_path

    def unzip_xml_gz(self, file_path_in: str) -> None:
        # Unzip the dataset if zipped
        if file_path_in.endswith(".gz"):
            file_path_out = file_path_in[:-3]
            if os.path.isfile(file_path_out):
                print("No .gz unpacked, XML file already exists.")
            else:
                with gzip.open(file_path_in, "rb") as f_in, open(file_path_out, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                print(f"Saved file {file_path_out}")

    def download_paper(self):
        pass

    def get_author_by_id(self):
        pass

    def get_venue_by_id(self):
        pass

    def get_paper_by_id(self):
        pass
