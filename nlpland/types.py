from enum import Enum

Url = str


class AccessType(str, Enum):
    OPEN = "oa"
    CLOSED = "closed"
