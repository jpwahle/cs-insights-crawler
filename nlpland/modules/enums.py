from enum import Enum


class ExtractionMethod(Enum):
    GROBID = "grobid"
    ANTHOLOGY = "anthology"
    RULEBASED = "rulebased"


class TypeOfPaper(Enum):
    JOURNAL = "journal"
    CONFERENCE = "conference"
    DEMO = "demo"
    WORKSHOP = "workshop"
    POSTER = "poster"
    TUTORIAL = "tutorial"
    DOCTORAL_CONSORTIUM = "doctoral_consortium"
    OTHER = "other"


class ShortLong(Enum):
    SHORT = "short"
    LONG = "long"
    UNKNOWN = "unknown"
