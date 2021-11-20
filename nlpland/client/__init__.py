""".. include:: CLIENT.md"""

from nlpland.client.backend import BackendClient, backend_schemas  # type: ignore
from nlpland.client.dblp import DBLPClient  # type: ignore

__all__ = ["DBLPClient", "BackendClient", "backend_schemas"]
