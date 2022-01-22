"""This module implements a client to communicate with the NLP-Land-backend."""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, TypeVar

from nlpland.client.backend.schemas import StatusSchema
from nlpland.client.generic.genericclient import GenericApiClient
from nlpland.data import Dataset
from nlpland.log import LogMixin
from nlpland.types import Url

T = TypeVar("T", bound="BackendClient")


class BackendClient(GenericApiClient, LogMixin):
    """A client to interact with NLP-Land-backend

    Args:
        GenericApiClient (Any): A shared generic client class.
        LogMixin (Any): A shared log mixin class.
    """

    @property
    def access_token(self: T) -> str:
        self._access_token = self._login()
        return self._access_token

    @property
    def version(self: T) -> Optional[str]:
        status = self._status()
        if status:
            return status.version
        return None

    def __init__(self: T, base_url: Url, **kwargs: Any) -> None:
        super(BackendClient, self).__init__(base_url, **kwargs)

    def get_latest_timestamps(self: T, **kwargs: Dict[str, Any]) -> datetime:
        # TODO Implement request for latest timestamp per category
        return datetime.now() - timedelta(weeks=54 * 100)

    def store(
        self: T,
        dataset: Dataset,
    ) -> None:
        # TODO: Run queries asynchronously with aiohttp

        # TODO: Create venues and affiliations first as authors and publications depend on them.

        # TODO: Update venues and affiliations in authors and publications with returned mongo ids

        # TODO: Create second as publications depend on them.

        # TODO: Update authors in publications with returned mongo ids

        # TODO: Create publications.
        raise NotImplementedError()
        # for paper in dataset.papers:
        #     self.post(url=f"/api/{self.version}/papers", data=paper.__dict__)

    def _login(self: T) -> str:
        # TODO: Implement token retrieval with environment credentials
        return "abcdefghijklmnopqrstuvwxyz"

    def _status(self: T) -> Optional[StatusSchema]:
        res, status = self.get(url="/api/status", headers={"content-type": "application/json"})
        res_schema: StatusSchema = res.json()
        if status == 200:
            return res_schema
        return None
