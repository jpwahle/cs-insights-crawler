"""This module includes all model schmeas from the backend database."""
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from typing import List


@dataclass
class BackendSchema:
    id: str


@dataclass
class Author(BackendSchema):
    dblpId: str
    fullname: str
    affiliations: List[str]
    timestamp: datetime
    email: str


@dataclass
class Venue(BackendSchema):
    dblpId: str
    fullname: str
    affiliations: List[str]
    timestamp: datetime
    email: str


@dataclass
class Affiliation(BackendSchema):
    dblpId: str
    fullname: str
    affiliations: List[str]
    timestamp: datetime
    email: str


@dataclass
class Publication(BackendSchema):
    dblpId: str
    fullname: str
    affiliations: List[str]
    timestamp: datetime
    email: str


backend_schemas = SimpleNamespace(
    **{
        "Author": Author,
        "Venue": Venue,
        "Affiliation": Affiliation,
        "Publication": Publication,
    }
)
