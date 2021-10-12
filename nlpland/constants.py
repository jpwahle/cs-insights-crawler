"""This module provides some constants that are used throughout the project.

These do not have to be changed by the user."""
from datetime import datetime
from typing import Union

MISSING_PAPERS = "missing_papers.txt"
COLUMN_ABSTRACT = "NE abstract"
COLUMN_ABSTRACT_SOURCE = "NE abstract source"
# UNICODE_COLUMN = "NE encoding issue flag"
ABSTRACT_SOURCE_ANTHOLOGY = "anth"
ABSTRACT_SOURCE_RULE = "rule"
CURRENT_TIME = str.replace(datetime.now().isoformat(timespec="seconds"), ":", "-")
FILTER_DATATYPES = Union[str, int, bool]
