""".. include:: CLIENT.md"""

from .backend import (
    AffiliationSchema,
    AuthorSchema,
    BackendClient,
    BackendSchema,
    PublicationSchema,
    VenueSchema,
)
from .dblp import DBLPClient
from .generic import GenericApiClient
from .grobid import GrobidClient

__all__ = [
    "BackendClient",
    "DBLPClient",
    "GrobidClient",
    "AuthorSchema",
    "VenueSchema",
    "PublicationSchema",
    "AffiliationSchema",
    "BackendSchema",
    "GenericApiClient",
]
