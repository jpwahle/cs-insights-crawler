from datetime import datetime
from typing import List, Tuple, Union

from csinsights.client.dblpclient import DBLPClient  # type: ignore
from csinsights.types import IGNORE_DBLP_KEYS, AccessType, DatasetJsonDict


def transform_dataset_to_scrapy(
    dataset_dict: DatasetJsonDict,
    dblp_access_type: AccessType,
    **kwargs: Union[str, int, bool, datetime, AccessType]
) -> Tuple[List[str], List[str]]:
    """Transforms the DBLP dataset object into two lists for the crawler

    Args:
        dataset_dict (DatasetJsonDict): The dataset dict of DBLP
        dblp_access_type (AccessType): The access type to filter for

    Returns:
        Tuple[List[str], List[str]]: Two lists, the dblp_keys which are the unique keys,
         and the pdf urls to crawl
    """
    start_urls = []
    dblp_keys = []

    condition_has_type = (
        lambda x: (dblp_access_type == AccessType.ALL)  # Always true
        or (
            dblp_access_type == AccessType.CLOSED  # Closed
            and type(x["ee"]) is dict  # Is there a pdf link with acces info?
            and "@type" in x["ee"].keys()  # Does it have an access type?
            and x["ee"]["@type"] == dblp_access_type  # Is the access type closed?
            or "ee" in x  # Or is it just any paper with a link (default is closed)?
        )
        or (
            dblp_access_type == AccessType.OPEN  # Open
            and type(x["ee"]) is dict  # Is there a pdf link with acces info?
            and "@type" in x["ee"].keys()  # Does it have an access type?
            and x["ee"]["@type"]
            == dblp_access_type  # Is the access type open (everything else is closed by default)?
        )
    )

    for key in dataset_dict.keys():
        # Get open access pdfs
        s = [
            el["ee"]["#text"]
            for el in dataset_dict[key]
            if condition_has_type(el) and el not in IGNORE_DBLP_KEYS
        ]
        # Get dblp keys
        d = [
            el["@key"]
            for el in dataset_dict[key]
            if condition_has_type(el) and el not in IGNORE_DBLP_KEYS
        ]
        # Put into the large list
        start_urls.extend(s)
        dblp_keys.extend(d)

    return dblp_keys, start_urls


__all__ = ["DBLPClient"]
