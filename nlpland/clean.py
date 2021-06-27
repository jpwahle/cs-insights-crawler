import nltk
import regex as re
from string import punctuation
from nltk.corpus import words, stopwords
from nltk.stem import WordNetLemmatizer
from typing import List


def clean_paper_id(paper_id: str) -> str:
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str) -> str:
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


def preprocess_text(text: str, language_vocabulary, lemmatizer, stopwords):
    text = clean_newline_hyphens(text, language_vocabulary)
    tokens = tokenize_and_lemmatize(text, lemmatizer)
    tokens = remove_stopwords(tokens, stopwords)
    return tokens


def clean_newline_hyphens(input_: str, language_vocabulary):
    # does not remove stopwords, punctuation
    input_ = input_.lower()
    for match in re.findall(r"[\s]+(\S*-\n\S*)[\s]+", input_, overlapped=True):
        # regex: start and end with whitespace
        # arbitrary amount of chars with -\n somewhere in it
        new_match = match.replace("-\n", "")
        new_match = new_match.strip(punctuation)
        if new_match in language_vocabulary:
            input_ = input_.replace(match, new_match)
        else:
            input_ = input_.replace(match, match.replace("-\n", "-"))
    return input_


def tokenize_and_lemmatize(text, lemmatizer):
    tokens = nltk.word_tokenize(text)
    return [lemmatizer.lemmatize(token) for token in tokens]


def get_english_words():
    return set(words.words())


def get_stopwords_and_more():
    stops = stopwords.words('english')
    stops += [char for char in punctuation]
    return set(stops)


def get_lemmatizer():
    return WordNetLemmatizer()


# TODO add download nltk corpus

# TODO remove numbers everywhere

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def remove_stopwords(tokens: List[str], stopwords):
    return [token for token in tokens if token not in stopwords and not is_number(token)]
