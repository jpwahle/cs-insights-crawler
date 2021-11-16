import gzip
import hashlib
from io import BufferedReader
import os
import shutil
from typing import Optional, List

import requests
from bs4 import BeautifulSoup
from lxml import etree
from lxml.etree import XMLSyntaxError
from tqdm import tqdm
from xmldiff import main, formatting

# region helpers
def md5_in_chunks(file: BufferedReader, block_size=2 ** 20):
    md5 = hashlib.md5()
    while True:
        data = file.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


# endregion


class DBLPClient:
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

    def latest_url_for_extension(self, extension: str, n: int = 1) -> str:
        iterator = (url for url in self.releases if url.endswith(extension))
        latest_url = ""
        for _ in range(n):
            latest_url = next(iterator)
            print(latest_url)
        return latest_url

    def check_md5(self, filepath: str, md5: str) -> bool:
        return self.local_md5(filepath) == md5

    def local_md5(self, filepath: str) -> str:
        with open(filepath, "rb") as f:
            return md5_in_chunks(f)

    def remote_md5(self, file_url: str) -> str:
        md5_url = file_url + ".md5"
        page = requests.get(md5_url).text
        md5 = page.partition(" ")[0]
        return md5

    def download_in_chunks(self, url: str, file_path: str, chunk_size: int = 1024) -> None:
        response = requests.get(url, stream=True)
        total_size_in_bytes = int(response.headers.get("content-length", 0))

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
        md5 = self.remote_md5(file_url)
        # If cached file is already there and has correct md5, skip
        if os.path.isfile(file_path) and self.check_md5(file_path, md5):
            print("No .xml.gz downloaded, file already exists and md5 matches.")
        else:
            # Download the dataset
            self.download_in_chunks(file_url, file_path)
            print(f"Saved file {file_path}")
            if not self.check_md5(file_path, md5):
                print("Hash of downloaded file does not match.")
        return file_path

    def unzip_xml_gz(self, file_path_in: str) -> str:
        # Unzip the dataset if zipped
        print("Unzipping file...")
        if file_path_in.endswith(".gz"):
            file_path_out = file_path_in[:-3]
            # Always unzip only then it is guranteed that the md5 was matched
            # Otherwise when the process is canceled we can not guarantee the file is not corrupted
            with gzip.open(file_path_in, "rb") as f_in, open(file_path_out, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            print(f"Saved file {file_path_out}")
            return file_path_out

    def validate_xml(self, file_path_xml: str) -> None:
        # dtd needs to be in the same directory as the xml
        try:
            parser = etree.XMLParser(dtd_validation=True)
            etree.parse(file_path_xml, parser)
            print("XML matches DTD.")
        except XMLSyntaxError as e:
            print("XML does not match DTD.")
            print(e)

    def create_diff(self, file_path_1, file_path_2):
        # Main calculation of diff

        # Apply all filters before the actual diff to save time

        if os.path.isfile(file_path_2):
            diff = main.diff_files(file_path_1, file_path_2, formatter=formatting.XMLFormatter())
            print(diff)
        else:
            # first run, everything is new
            pass

    def download_paper(self):
        pass

    def get_author_by_id(self):
        pass

    def get_venue_by_id(self):
        pass

    def get_paper_by_id(self):
        pass
