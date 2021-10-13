"""This module provides functions to clean the input from the a dataset."""
import string
from typing import List, Set

import nltk
import regex as re


def clean_paper_id(paper_id: str) -> str:
    """Clean the paper id, by removing or replacing symbols that are not allowed in a file name.

    Args:
        paper_id: Original id of the paper.

    Returns:
        Cleaned id of the paper.
    """
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str) -> str:
    """Clean the venue name, by removing or replacing symbols that are not allowed in a file name.

    Args:
        venue_name: Original venue name.

    Returns:
        Cleaned venue name.
    """
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


def preprocess_text(
    text: str,
    language_vocabulary: Set[str],
    lemmatizer: nltk.WordNetLemmatizer,
    stopwords: Set[str],
) -> List[str]:
    """Preprocess a given text by removing newline hyphens, tokenizing, lemmatizing and removing
     stopwords.

    Args:
        text: Text to preprocess.
        language_vocabulary: Vocabulary (set of words) used for lookup to remove newline hyphens.
        lemmatizer: Lemmatizer used to lemmatize the tokens.
        stopwords: Set of stopwords to remove.

    Returns:
        List of tokens/words.
    """
    text = newline_hyphens(text, language_vocabulary)
    tokens = tokenize_and_lemmatize(text, lemmatizer)
    tokens = remove_stopwords(tokens, stopwords)
    return tokens


def newline_hyphens(text: str, language_vocabulary: Set[str]) -> str:
    """Remove hyphens followed by a newline "-\n", if the sequence without hyphen is in the given
    vocabulary, otherwise leave the hyphen.

    Always remove the newline character "\n".
    The regex used will match a whitespace character at the start and end of the sequence with an
    arbitrary amount of characters and "-\n" somewhere in between.

    Goal:
        char-\n
        acter
        -> dictionary
        open-\n
        source
        -> open-source

    Args:
        text: Text to process.
        language_vocabulary: Vocabulary to check the sequences against.

    Returns:
        Text without "-\n" sequences.
    """
    text = text.lower()
    for match in re.findall(r"[\s]+(\S*-\n\S*)[\s]+", text, overlapped=True):
        new_match = match.replace("-\n", "")
        new_match = new_match.strip(string.punctuation)
        if new_match in language_vocabulary:
            text = text.replace(match, new_match)
        else:
            text = text.replace(match, match.replace("-\n", "-"))
    return text


def tokenize_and_lemmatize(text: str, lemmatizer: nltk.WordNetLemmatizer) -> List[str]:
    """Tokenize and lemmatize the given text.

    Args:
        text: Text to process.
        lemmatizer: Lemmatizer used to lemmatize the tokens.

    Returns:
        List of lemmatized tokens.
    """
    nltk_resource("tokenizers/punkt")
    nltk_resource("corpora/wordnet")
    tokens = nltk.word_tokenize(text)
    return [lemmatizer.lemmatize(token) for token in tokens]


def english_words() -> Set[str]:
    """Return a set of english words from the nltk corpus "words".

    Returns:
        Set of english words.
    """
    nltk_resource("corpora/words")
    return set(nltk.corpus.words.words())


def stopwords_and_more() -> Set[str]:
    """Return a set of stopwords from the nltk corpus "stopwords" including punctuation from
    "string.punctuation".

    Returns:
        List of stopwords including punctuation.
    """
    nltk_resource("corpora/stopwords")
    stops = nltk.corpus.stopwords.words("english")
    stops += list(string.punctuation)
    return set(stops)


def get_lemmatizer() -> nltk.WordNetLemmatizer:
    """Return the WordNet lemmatizer from nltk.

    Returns:
        WordNet lemmatizer from nltk.
    """
    return nltk.stem.WordNetLemmatizer()


def is_number(word: str) -> bool:
    """Check if string/words is a number.

    Args:
        word: Word to check.

    Returns:
        True, if given word is a number.
    """
    try:
        float(word)
        return True
    except ValueError:
        return False


def remove_stopwords(tokens: List[str], stopwords: Set[str]) -> List[str]:
    """Remove stopwords and numbers from a given list of tokens.

    Args:
        tokens: List of tokens to process.
        stopwords: Set of stopwords to remove.

    Returns:
        List of tokens without stopwords.
    """
    return [
        token for token in tokens if token not in stopwords and not is_number(token)
    ]


def nltk_resource(name: str) -> None:
    """Download an nltk resource, if it was not already downloaded.

    Args:
        name: Name of the resource (e.g.: "corpora/words")
    """
    try:
        nltk.data.find(name)
    except LookupError:
        nltk.download(name.split("/")[-1])
