from mongoengine import Document, CASCADE
from mongoengine.fields import (
    StringField,
    ListField,
    ReferenceField,
    IntField,
    FloatField,
    DateTimeField,
    EnumField,
    BooleanField,
)

from nlpland.modules.enums import ExtractionMethod, TypeOfPaper, ShortLong

class Topic(Document):
    meta = {"collection": "topics"}
    identifier = StringField(required=True)
    keywords = ListField(StringField(required=True), required=True)
    keywordsWeighting = ListField(FloatField(required=True), required=True)
    numberOfTokens = IntField(min_value=0, max_value=None, required=True)


class Institution(Document):
    meta = {"collection": "institutions"}
    name = StringField(required=True)
    country = StringField(required=True)
    city = StringField(
        required=False
    )  # We can derive the city by using wikidata and the instiution name


class Author(Document):
    meta = {"collection": "authors"}
    name = StringField(
        required=True
    )  # The most recent one in a published paper
    affiliations = ListField(
        ReferenceField(
            "Institution", reverse_delete_rule=CASCADE, required=True
        ),
        required=False,
    )
    citations = IntField(min_value=0, max_value=None, required=True)
    citationsTimestamp = DateTimeField(required=True)
    email = StringField(
        required=False
    )  # The most recent one in a published paper


class VenueDetails(Document):
    year = DateTimeField(required=True)
    callForPapersText = StringField(required=False)
    topics = ListField(
        ReferenceField(document_type="Topic", reverse_delete_rule=CASCADE),
        required=False,
    )


class Venue(Document):
    meta = {"collection": "venues"}
    name = StringField(required=True)
    acronym = StringField(max_length=140)
    venueCodes = ListField(StringField(required=True))
    venueDetails = ListField(
        ReferenceField("VenueDetails", reverse_delete_rule=CASCADE),
        required=False,
    )


class Paper(Document):
    meta = {"collection": "papers"}
    title = StringField(max_length=140, required=True)
    abstractText = StringField(required=True)
    abstractExtractor = EnumField(enum=ExtractionMethod, required=True)
    typeOfPaper = EnumField(
        enum=TypeOfPaper, default=TypeOfPaper.OTHER, required=True
    )
    shortOrLong = EnumField(
        enum=ShortLong, default=ShortLong.UNKNOWN, required=True
    )

    atMainConference = BooleanField(default=False, required=True)
    isSharedTask = BooleanField(default=False, required=True)
    isStudentPaper = BooleanField(default=False, required=True)

    # Discuss with Lennart: Which preprocessing methods to use?
    # abstract_preprocessed = StringField()

    doi = StringField(required=False)
    # preProcessingGitHash = StringField(required=True)
    # PDFUrl = StringField(required=True)
    ABSUrl = StringField(required=True)

    datePublished = DateTimeField(required=True)
    citations = IntField(min_value=0, max_value=None, required=True)
    # citationsTimestamp = DateTimeField(required=True)

    # paperTopics = ListField(
        # ReferenceField("Topic", reverse_delete_rule=CASCADE), required=True
    # )
    # authors = ListField(
    #     ReferenceField("Author", reverse_delete_rule=CASCADE, required=True)
    # )
    # firstAuthor = ReferenceField(
    #     document_type="Author", reverse_delete_rule=CASCADE, required=True
    # )
    # venue = ReferenceField("Venue", reverse_delete_rule=CASCADE, required=True)

    # titleEmbedding = ListField(FloatField(required=True), required=True)
    # abstractEmbedding = ListField(FloatField(required=True), required=True)
    # embeddingModelName = StringField(max_length=140, required=True)

