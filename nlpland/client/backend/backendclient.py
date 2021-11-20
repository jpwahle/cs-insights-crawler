"""This module implements a client to communicate with the NLP-Land-backend."""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, TypeVar

from nlpland.client.genericclient import ApiClient  # type: ignore
from nlpland.log.logger import LogMixin
from nlpland.types import Url  # type: ignore

T = TypeVar("T", bound="BackendClient")


class BackendClient(ApiClient, LogMixin):
    def __init__(self: T, cache_dir: Path, base_url: Url, **kwargs: Any) -> None:
        self.cache_dir = cache_dir
        super(BackendClient, self).__init__(base_url, **kwargs)

    def get_latest_timestamps(self: T, **kwargs: Dict[str, Any]) -> datetime:
        # TODO Implement request for latest timestamp per category
        return datetime.now() - timedelta(days=1000)

    def run_queries(self: T) -> None:
        pass
