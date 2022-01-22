"""This module includes all model schmeas from the backend database."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union

from nlpland.types import ExtractorType, PaperType, Url


@dataclass
class BackendSchema:
    """Base class for all schemas."""

    id: Optional[str]


@dataclass
class AuthorSchema(BackendSchema):
    """The author schemma from the backend database.

    Args:
        BackendSchema (Any): General backend schema every schema inherits from.
    """

    dblpId: str
    fullname: str
    affiliations: List[str]
    email: str


@dataclass
class VenueSchema(BackendSchema):
    """The venue schemma from the backend database.

    Args:
        BackendSchema (Any): General backend schema every schema inherits from.
    """

    names: List[str]
    acronyms: List[str]
    venueCodes: List[str]
    venueDetails: List[Dict[str, Union[str, datetime]]]
    dblpId: str


@dataclass
class AffiliationSchema(BackendSchema):
    """The affiliation schemma from the backend database.

    Args:
        BackendSchema (Any): General backend schema every schema inherits from.
    """

    name: str
    country: str
    lat: float
    lng: float
    city: Optional[str]
    addressline: Optional[str]
    postcode: Optional[str]
    countrycode: Optional[str]
    timestamp: datetime


@dataclass
class PublicationSchema(BackendSchema):
    """The publication schemma from the backend database.

    Args:
        BackendSchema (Any): General backend schema every schema inherits from.
    """

    title: str
    abstractText: str
    abstractExtractor: ExtractorType
    typeOfPaper: PaperType
    authors: List[str]

    doi: str
    preProcessingGitHash: str
    pdfUrl: Url
    absUrl: Url
    volume: Optional[str]

    datePublished: datetime
    citationInfoTimestamp: datetime
    cites: List[str]

    venues: List[str]
    dblpId: str


@dataclass
class StatusSchema(BackendSchema):
    """The status schemma from the backend endpoint.

    Args:
        BackendSchema (Any): General backend schema every schema inherits from.
    """

    version: str
    timestamp: datetime
    isAlive: bool
