from typing import Dict, List

from nlpland.data.clean import clean_paper_id
import pytest


@pytest.fixture()
def test_object() -> Dict[str, List[str]]:
    return {
        "paper_ids": ["S13-1042", "2020.acl-main.178"],
    }


def test_clean_paper_id(test_object: Dict[str, List[str]]) -> None:
    assert clean_paper_id(test_object["paper_ids"][0]) == test_object["paper_ids"][0]
    assert clean_paper_id(test_object["paper_ids"][1]) == "2020_acl-main_178"
