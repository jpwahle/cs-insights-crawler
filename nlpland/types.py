"""This module implements the types used in the nlpland package."""
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# region exceptions


class ServerUnavailableException(Exception):
    """An exception when the grobid server is not running.

    Args:
        Exception (Any): Inherits from general Exception
    """

    pass


# region exceptions

# region enums


class AccessType(str, Enum):
    """The access type of a resource."""

    OPEN = "oa"
    CLOSED = "closed"


class ExtractorType(str, Enum):
    """The type of Extractor."""

    GROBID = "grobid"
    RULEBASED = "rulebased"


class PaperType(str, Enum):
    """The type of a paper."""

    JOURNAL = "journal"
    CONFERENCE = "conference"
    DEMO = "demo"
    WORKSHOP = "workshop"
    POSTER = "poster"
    TUTORIAL = "tutorial"
    DOCTORALCONSORTIUM = "doctoralconsortium"
    MASTERSTHESIS = "mastersthesis"
    PHDTHESIS = "phdthesis"
    OTHER = "other"


class ValidGrobidServices(str, Enum):
    """Enum of valid services"""

    processFulltextDocument = "processFulltextDocument"
    processHeaderDocument = "processHeaderDocument"
    processReferences = "processReferences"
    processCitationList = "processCitationList"


# endregion

# region standard types

Url = str

DatasetJsonDict = Dict[str, List[Dict[str, Any]]]

FilterFunction = Callable[[DatasetJsonDict], DatasetJsonDict]

PdfExtractionFn = Callable[
    [
        ValidGrobidServices,
        Path,
        int,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        bool,
        Optional[Path],
    ],
    None,
]

# endregion