import mongoengine as db
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

# connect to the mongoDB in the way you wish
DB_URI = ""
db.connect(host = DB_URI)

import pandas as pd
from nlpland.modules.enums import ExtractionMethod, TypeOfPaper, ShortLong
from nlpland.modules.models import Paper, Author, Venue, Institution, Topic


# getAbstract
def getAbstractText(df : pd.DataFrame):
    if pd.isnull(df[1]["NE abstract"]):
            return ""
    return df[1]["NE abstract"]

# getAbstractExtractor
def getAbstractExtractor(df : pd.DataFrame):
    if df[1]["NE abstract source"] == "anth":
        return ExtractionMethod.ANTHOLOGY
    elif df[1]["NE abstract source"] == "rule":
        return ExtractionMethod.RULEBASED
    return ExtractionMethod.GROBID

# // get Title
def getTitle(df : pd.DataFrame):
    return df[1]["AA title"]

# get TypeOfPaper
def getTypeOfPaper(df : pd.DataFrame):
    if df[1]["NS tutorial flag"]:
        return TypeOfPaper.TUTORIAL
    elif df[1]["NS demo flag"]:
        return TypeOfPaper.DEMO
    elif df[1]["NS workshop flag"]:
        return TypeOfPaper.WORKSHOP
    elif df[1]["NS doctoral consortium flag"]:
        return TypeOfPaper.DOCTORAL_CONSORTIUM
    elif df[1]["NS conference flag"]:
        return TypeOfPaper.CONFERENCE
    elif df[1]["NS long paper flag"]:
        return TypeOfPaper.POSTER
    return TypeOfPaper.OTHER

# get shortOrLong
def getShortOrLong(df: pd.DataFrame):
    if df[1]["NS long paper flag"]:
        return ShortLong.LONG
    elif df[1]["NS short paper flag"]:
        return ShortLong.SHORT
    return ShortLong.UNKNOWN

# get atMainConference
def getAtMainConference(df : pd.DataFrame):
    return df[1]["NS main conference flag"]

# get isSharedTask
def getIsSharedTask(df : pd.DataFrame):
    return df[1]["NS shared task flag"]

# get isStudentPaper
def getIsStudentPaper(df : pd.DataFrame):
    return df[1]["NS student paper flag"]

# get doi
def getDoi(df : pd.DataFrame):
    return df[1]["AA doi"]

# get ABSUrl
def getABSUrl(df : pd.DataFrame):
    return df[1]["AA url"]

# get datePublished
def getDatePublished(df : pd.DataFrame):
        return pd.to_datetime(str(df[1]["AA year of publication"])  + str(df[1]["AA month of publication"].split('–')[0]), format='%Y%B')


# get citations
def getCitations(df : pd.DataFrame):
    return df[1]["GS citations"]


def store(df : pd.DataFrame):
    for row in df.head().iterrows():
        abstractText = getAbstractText(row)
        abstractExtractor = getAbstractExtractor(row)
        title = getTitle(row)
        typeOfPaper = getTypeOfPaper(row)
        shortOrLong = getShortOrLong(row)
        atMainConference = getAtMainConference(row)
        isSharedTask = getIsSharedTask(row)
        isStudentPaper = getIsStudentPaper(row)
        doi = getDoi(row)
        datePublished = getDatePublished(row)
        ABSUrl = getABSUrl(row)
        datePublished = getDatePublished(row)
        citations = getCitations(row)
        paper = Paper(abstractText = abstractText, abstractExtractor = abstractExtractor,title = title, typeOfPaper = typeOfPaper, shortOrLong = shortOrLong, atMainConference = atMainConference, 
            isStudentPaper = isStudentPaper, datePublished = datePublished, ABSUrl = ABSUrl, citations = citations)
        if not pd.isnull(doi):
            paper.doi = doi
        paper.save()


