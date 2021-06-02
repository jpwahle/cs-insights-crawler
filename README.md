# NLPLand

This repository is part of the project titled "NLPLand and its Secrets".
The project is within the scope of the Information Retrieval course at the Bergische University of Wuppertal in the summer semester of 2021.
The following project description should give a broad overview over the project, but is subject to change.

### Project Description
The ACL Anthology (AA) is the largest single repository of thousands of articles on Natural Language Processing (NLP) and Computational Linguistics (CL). It contains valuable metadata (e.g. venues, authors’ name, title) that can be used to better understand the field. NLP Scholar, uses this data to examine the literature to identify broad trends in productivity, focus, and impact. We want to extend this analysis to specific components in NLP publications.


## Installation & Setup

### poetry
First download poetry as explained here: https://python-poetry.org/docs/#installation

Next, clone the repository and navigate to the root folder `NLPLand` in a shell. Execute `poetry install` there. This will install all the dependencies this project needs.

(You need python 3.7 for this)

### .env
First you have to rename the file `empty.env` to `.env`. In the file you also have to set your variables.

Hint: All path variables can be either an absolute or relative path.

`PATH_PAPERS` is the path to the directory with the downloaded papers.

`PATH_DATASET` is the path to the `.txt` file of the NLP Scholar dataset. 

`PATH_DATASET_EXPANDED` is the path to the `.txt` file of the expanded dataset or where it is supposed to be saved.
