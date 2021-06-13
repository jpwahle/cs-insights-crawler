import nltk
import regex as re
from string import punctuation


def clean_paper_id(paper_id: str) -> str:
    return paper_id.replace(".", "_")


def clean_venue_name(venue_name: str) -> str:
    return venue_name.replace("*", "").replace("/", "_").replace(" ", "_")


def clean_and_tokenize(input_: str, language_vocabulary):
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

    tokens = nltk.word_tokenize(input_)
    # print(input)
    # print(tokens)
    return tokens


def venues_to_list(venues: str):
    venues_list = venues.split(',')
    venues_list = [venue.strip(" ") for venue in venues_list]
    return venues_list
