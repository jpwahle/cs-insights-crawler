"""This module implements a `XMLDataset` based on a `GenericDataset`."""
from typing import Any, Dict, List, Type, TypeVar

import xmltodict  # type: ignore
from lxml import etree

from nlpland.client.backend.schemas import BackendSchema
from nlpland.log.logger import LogMixin

T = TypeVar("T", bound="Transformer")


class Transformer(LogMixin):
    def __init__(self: T) -> None:
        super().__init__()

    @classmethod
    def convert_to_schema(  # type: ignore
        cls: Type[T],
        entities: List[etree._Element],
        author_schema: BackendSchema,
        venue_schema: BackendSchema,
        affiliation_schema: BackendSchema,
        publication_schema: BackendSchema,
        **kwargs: Any
    ) -> Dict[str, Any]:
        for entity in entities:
            xml_as_dict = xmltodict.parse(etree.tostring(entity))

            # TODO: Create venues and affiliations first as authors and publications depend on them.

            # TODO: Create authors second as publications depend on them.

            # TODO: Create publications last.

            cls.logger.info(xml_as_dict)

        return {}
