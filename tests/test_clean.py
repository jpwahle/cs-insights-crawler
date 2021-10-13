from typing import List

import nltk
import pytest

import nlpland.data.clean as clean_


@pytest.mark.parametrize(
    "paper_id, expected",
    [("S13-1042", "S13-1042"), ("2020.acl-main.178", "2020_acl-main_178")],
)
def test_clean_paper_id(paper_id: str, expected: str) -> None:
    assert clean_.clean_paper_id(paper_id) == expected


@pytest.mark.parametrize(
    "venue_name, expected",
    [
        ("*SEM", "SEM"),
        ("ROCLING/IJCLCLP", "ROCLING_IJCLCLP"),
        ("Student Research", "Student_Research"),
    ],
)
def test_clean_venue_name(venue_name: str, expected: str) -> None:
    assert clean_.clean_venue_name(venue_name) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (" char-\nacter ", " character "),
        ("\nchar-\nacter\t", "\ncharacter\t"),
        (" open-\nsource ", " open-source "),
        (" open-source ", " open-source "),
    ],
)
def test_newline_hyphens(text: str, expected: str):
    vocabulary = {"character"}
    assert clean_.newline_hyphens(text, vocabulary) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("hello world", ["hello", "world"]),
        ("hello world.", ["hello", "world", "."]),
        ("Hello world", ["Hello", "world"]),
        ("Hello worlds", ["Hello", "world"]),
    ],
)
def test_tokenize_and_lemmatize(text: str, expected: str):
    lemmatizer = clean_.get_lemmatizer()
    assert clean_.tokenize_and_lemmatize(text, lemmatizer) == expected


def test_english_words():
    words = clean_.english_words()
    assert isinstance(words, set)
    assert "character" in words


def test_stopwords_and_more():
    stopwords = clean_.stopwords_and_more()
    assert isinstance(stopwords, set)
    assert "and" in stopwords
    assert "." in stopwords
    assert "to" in stopwords


def test_get_lemmatizer():
    lemmatizer = clean_.get_lemmatizer()
    assert isinstance(lemmatizer, nltk.stem.WordNetLemmatizer)


@pytest.mark.parametrize(
    "word, expected",
    [
        ("hello world", False),
        ("42", True),
        ("1.2", True),
        ("1,4", False),
        ("3.1e5", True),
        ("0.00", True),
    ],
)
def test_is_number(word: str, expected: bool):
    assert clean_.is_number(word) == expected


@pytest.mark.parametrize(
    "tokens, expected",
    [
        (["to", "be", "or", "not", "to", "be"], []),
        (["42.67"], []),
        (["hello", "world"], ["hello", "world"]),
    ],
)
def test_remove_stopwords(tokens: List[str], expected: List[str]):
    stopwords = {"to", "be", "or", "not"}
    assert clean_.remove_stopwords(tokens, stopwords) == expected


# @pytest.mark.parametrize(
#     "name",
#     [
#         "corpora/words",
#         "tokenizer/punkt",
#     ],
# )
# def test_nltk_resource(mocker, name: str):
#     # stopwords = {"to", "be", "or", "not"}
#     print(type(mocker))
#     mocker.patch("nltk.data.find", side_effects=[LookupError])
#     assert clean_.nltk_resource(name) == LookupError
