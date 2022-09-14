"""The data processort class for the SemanticScholar dataset."""
import gzip
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, TypeVar, Union

import jsonlines
import pandas as pd
from tqdm import tqdm

from csinsights.log import LogMixin

T = TypeVar("T", bound="SemanticScholarDataProcessor")

s2filters = {
    "acl": "ACL",
    "dblp": "DBLP",
    "arxiv": "ArXiv",
    "pubmed": "PubMed",
    "pubmedcentral": "PubMedCentral",
}

unsupported_filters: List[str] = []


class SemanticScholarDataProcessor(LogMixin):
    """A data processor for

    Args:
        LogMixin (Any): A shared log mixin class.
    """

    def __init__(self: T, cache_dir: Path, **kwargs: Union[str, Path]) -> None:
        """Constructor the the SemanticScholarDataProcessor

        Args:
            self (T): This object.
            cache_dir (Path): The cache directory to store releases in.
        """
        self.cache_dir = cache_dir
        # A dict that stores the dataset name and its filtered data {"dataset_name": [...]}
        self.datasets: Dict[str, list] = defaultdict(list)

    def process_data(self: T, **kwargs: str) -> T:
        """Load and join the data from the releases.

        Args:
            self (T): This object.
        """
        # Collect all corpus ids from filtered papers. Some sentient metadata fields don't
        # have external ids (e.g. for DBLP). If we don't filter them out early, we will run into
        # memory issues later on
        filtered_corpusids: Set[str] = set()
        # First get all papers to get which paper ids are important to filter
        for filepath in self.cache_dir.glob("papers*.jsonl.gz"):
            # Read the data and filter it
            filtered = self._read_and_filter_jsonl_file(filepath, filtered_corpusids, **kwargs)
            filtered_corpusids.update([paper["corpusid"] for paper in filtered])
            self.datasets[str(filepath).split("/")[-1].split("_")[0]].extend(filtered)
        # Then get the remainder
        for filepath in self.cache_dir.glob("*.jsonl.gz"):
            if "papers" not in str(filepath):
                # Read the data and filter it
                filtered = self._read_and_filter_jsonl_file(filepath, filtered_corpusids, **kwargs)
                # Append it to the datasets dict
                self.datasets[str(filepath).split("/")[-1].split("_")[0]].extend(filtered)

        # Merge the datasets
        self._merge_datasets()
        # Filter the authors
        self._filter_authors()
        # Prepare the data for release
        self._prepare_for_release()
        # Return an instance of this object to make function calls available in a chain
        return self

    def _filter_authors(self: T) -> None:
        """Filter the authors according to the filtered dataset.

        Args:
            self (T): This object.
        """
        # Get all unique author ids from papers
        all_paper_authors = set()
        for paper in self.datasets["papers"]:
            for author in paper["authors"]:
                all_paper_authors.add(author["authorId"])

        # Filter authors
        self.datasets["authors"] = [
            author for author in self.datasets["authors"] if author["authorid"] in all_paper_authors
        ]

    def _merge_datasets(self: T) -> None:
        """Merge the datasets.

        Args:
            self (T): This object.
        """
        # Sort by corpusid
        for dataset in self.datasets:
            self.datasets[dataset] = sorted(
                self.datasets[dataset], key=lambda x: ("corpusid" in x, x.get("corpusid", None))
            )

        # Merge papers with sentient metadata
        for dataset in self.datasets:
            # Authors have to be filtered seperately and we always merge on papers
            if dataset != "authors" and dataset != "papers":
                # Update papers by joining the data (e.g., abstracts, citations, ...)
                # The final dataset will only contain "papers" and "authors"
                d: dict = defaultdict(dict)
                for doc in (self.datasets[dataset], self.datasets["papers"]):
                    for elem in doc:
                        d[elem["corpusid"]].update(elem)
                self.datasets["papers"] = list(d.values())

    def _read_and_filter_jsonl_file(
        self: T, filepath: Path, filtered_corpusids: set, **kwargs: Union[str, bool]
    ) -> List[dict]:
        """Read the data from a jsonl file.

        Args:
            self (T): This object.
            filtered_corpusids (set): A set of corpus ids. The rest can be filtered.
            filepath (Path): The path to the .jsonl.gz file.
        """
        # Check if any of the not supported features are used
        if any([kwargs[feature] for feature in unsupported_filters]):
            raise NotImplementedError(
                f"The following filters are not supported yet: {unsupported_filters}"
            )
        # Create Filters
        filters = []
        for arg in kwargs:
            if arg.startswith("s2_filter_") and kwargs[arg]:
                filters.append(s2filters[arg.split("_")[-1]])

        # Create filter condition by ids
        def check_condition(paper: dict) -> bool:
            return any(
                paper["externalids"][f] is not None
                if "externalids" in paper
                and paper["externalids"] is not None
                and f in paper["externalids"]
                else False
                for f in filters
            )

        docs = []
        # Open it
        with gzip.open(filepath, "rb") as f:
            for line in tqdm(f, miniters=10000, desc=f"Reading {filepath}"):
                # Read it
                doc = json.loads(line)
                if (
                    "openaccessinfo" in doc
                    and doc["openaccessinfo"] is not None
                    and "externalids" in doc["openaccessinfo"]
                ):
                    doc["externalids"] = doc["openaccessinfo"]["externalids"]
                    del doc["openaccessinfo"]
                # If it's authors or abstracts they don't include DBLP ids so we accept loading
                # also without the condition. But then we filter by corpusid to not overload
                # the memory. The filtered_corpusids are empty at first and get extended by the
                # filtered papers.
                if (
                    ("papers" in str(filepath) and check_condition(doc))
                    or "authors" in str(filepath)
                    or (not filtered_corpusids and "papers" not in str(filepath))
                    or doc["corpusid"] in filtered_corpusids
                ):
                    docs.append(doc)

        return docs

    def clean_cache(self: T) -> None:
        """Clean the cache directory.

        Args:
            self (T): This object.
        """
        for file in self.cache_dir.glob("*.jsonl.gz"):
            file.unlink()

    def _prepare_for_release(self: T) -> None:
        """Prepare the data for release.

        Args:
            self (T): This object.
        """
        # Change "url" key of authors to "s2url"
        for author in self.datasets["authors"]:
            author["s2url"] = author.pop("url")

    def _prepare_release_dir(self: T, release_dir: str = "") -> None:
        """Prepare the release directory.

        Args:
            self (T): This object.
            release_dir (str, optional): The release directory. Defaults to "".
        """
        # Create release dir
        if release_dir:
            os.makedirs(os.path.expanduser(release_dir), exist_ok=True)

    def to_jsonl(self: T, custom_path: str = "") -> None:
        """Export the data to a jsonl file.

        Args:
            self (T): This object.
            custom_path (str, optional): The custom path. Defaults to "".
        """
        # Prepare the release dir
        self._prepare_release_dir(custom_path)
        # Papers export
        with gzip.open(
            os.path.join(os.path.expanduser(custom_path), "papers.jsonl.gz"), "wb"
        ) as fp:
            json_writer = jsonlines.Writer(fp)  # type: ignore
            json_writer.write_all(self.datasets["papers"])
        # Authors export
        with gzip.open(
            os.path.join(os.path.expanduser(custom_path), "authors.jsonl.gz"), "wb"
        ) as fp:
            json_writer = jsonlines.Writer(fp)  # type: ignore
            json_writer.write_all(self.datasets["authors"])

    def to_csv(self: T, custom_path: str = "") -> None:
        """Export the data to a csv file.

        Args:
            self (T): This object.
            custom_path (str, optional): The custom path. Defaults to "".
        """
        # Prepare the release dir
        self._prepare_release_dir(custom_path)
        # Create dataframes
        papers_df = pd.json_normalize(self.datasets["papers"])
        authors_df = pd.json_normalize(self.datasets["authors"])
        # Save to csv
        papers_df.to_csv(
            os.path.join(os.path.expanduser(custom_path), "papers.csv.gz"),
            index=False,
            sep="\t",
            compression="gzip",
            line_terminator="\r\n",
        )
        authors_df.to_csv(
            os.path.join(os.path.expanduser(custom_path), "authors.csv.gz"),
            index=False,
            sep="\t",
            compression="gzip",
            line_terminator="\r\n",
        )
