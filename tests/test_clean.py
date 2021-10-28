from typing import List

import nltk
import pytest
from pytest_mock import MockerFixture

from nlpland.data import clean


@pytest.mark.parametrize(
    "paper_id, expected",
    [("S13-1042", "S13-1042"), ("2020.acl-main.178", "2020_acl-main_178")],
)
def test_clean_paper_id(paper_id: str, expected: str) -> None:
    assert clean.clean_paper_id(paper_id) == expected


@pytest.mark.parametrize(
    "venue_name, expected",
    [
        ("*SEM", "SEM"),
        ("ROCLING/IJCLCLP", "ROCLING_IJCLCLP"),
        ("Student Research", "Student_Research"),
    ],
)
def test_clean_venue_name(venue_name: str, expected: str) -> None:
    assert clean.clean_venue_name(venue_name) == expected


def test_preprocess_text(mocker: MockerFixture) -> None:
    text = "Hello wor-\nld!\n"
    text2 = "Hello world!"
    language_vocabulary = {"hello", "world"}
    tokens = ["hello", "world", "."]
    tokens2 = ["hello", "world"]
    mocker.patch("nltk.stem.WordNetLemmatizer")
    lemmatizer = nltk.stem.WordNetLemmatizer()
    stopwords = {"!"}

    hyphens = mocker.patch("nlpland.data.clean.newline_hyphens", return_value=text2)
    tokenize = mocker.patch("nlpland.data.clean.tokenize_and_lemmatize", return_value=tokens)
    remove = mocker.patch("nlpland.data.clean.remove_stopwords", return_value=tokens2)

    result = clean.preprocess_text(text, language_vocabulary, lemmatizer, stopwords)
    hyphens.assert_called_once_with(text, language_vocabulary)
    tokenize.assert_called_once_with(text2, lemmatizer)
    remove.assert_called_once_with(tokens, stopwords)
    assert result == tokens2


@pytest.mark.parametrize(
    "text, expected",
    [
        (" char-\nacter ", " character "),
        ("\nchar-\nacter\t", "\ncharacter\t"),
        (" open-\nsource ", " open-source "),
        (" open-source ", " open-source "),
    ],
)
def test_newline_hyphens(text: str, expected: str) -> None:
    vocabulary = {"character"}
    assert clean.newline_hyphens(text, vocabulary) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("hello world", ["hello", "world"]),
        ("hello world.", ["hello", "world", "."]),
        ("Hello world", ["Hello", "world"]),
        ("Hello worlds", ["Hello", "world"]),
    ],
)
def test_tokenize_and_lemmatize(text: str, expected: str) -> None:
    lemmatizer = clean.get_lemmatizer()
    assert clean.tokenize_and_lemmatize(text, lemmatizer) == expected


def test_english_words() -> None:
    words = clean.english_words()
    assert isinstance(words, set)
    assert "character" in words


def test_stopwords_and_more() -> None:
    stopwords = clean.stopwords_and_more()
    assert isinstance(stopwords, set)
    assert "and" in stopwords
    assert "." in stopwords
    assert "to" in stopwords


def test_get_lemmatizer() -> None:
    lemmatizer = clean.get_lemmatizer()
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
def test_is_number(word: str, expected: bool) -> None:
    assert clean.is_number(word) == expected


@pytest.mark.parametrize(
    "tokens, expected",
    [
        (["to", "be", "or", "not", "to", "be"], []),
        (["42.67"], []),
        (["hello", "world"], ["hello", "world"]),
    ],
)
def test_remove_stopwords(tokens: List[str], expected: List[str]) -> None:
    stopwords = {"to", "be", "or", "not"}
    assert clean.remove_stopwords(tokens, stopwords) == expected


def test_nltk_resource(mocker: MockerFixture) -> None:
    find = mocker.patch("nltk.data.find")
    download = mocker.patch("nltk.download")

    resource = "corpora/words"
    clean.nltk_resource(resource)
    find.assert_called_once_with(resource)
    download.assert_not_called()

    find.reset_mock()
    find.side_effect = LookupError()
    resource = "tokenizer/punkt"
    clean.nltk_resource(resource)
    find.assert_called_once_with(resource)
    download.assert_called_once_with("punkt")
