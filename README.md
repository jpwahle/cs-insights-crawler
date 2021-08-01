# NLPLand

This repository is part of the project titled "NLPLand and its Secrets".
The project is within the scope of the Information Retrieval course at the Bergische University of Wuppertal in the summer semester of 2021.
The following project description should give a broad overview over the project, but is subject to change.

### Project Description
The ACL Anthology (AA) is the largest single repository of thousands of articles on Natural Language Processing (NLP) and Computational Linguistics (CL). It contains valuable metadata (e.g. venues, authors’ name, title) that can be used to better understand the field. NLP Scholar, uses this data to examine the literature to identify broad trends in productivity, focus, and impact. We want to extend this analysis to specific components in NLP publications.

## Installation & Setup
## poetry
First download poetry as explained here: https://python-poetry.org/docs/#installation

Also make sure you have python 3.7 installed.

Next, clone the repository and navigate to the root folder `NLPLand` in a shell.
Execute `poetry install` there.
This will install all the dependencies this project needs.
If you are in a virtual environment it will install all dependencies there, otherwise it will create a new one.
(Should poetry not be able to find a python 3.7 installation, specify the path using `poetry env use <path>` to create a venv.)

If you were not already in a venv, execute `poetry shell` to activate the newly created one.
(If the command does not work, try to activate the venv manually.) 

### .env
You have to rename the file `empty.env` to `.env`. In this file you have to set your variables.  (Hint: All path variables can be either an absolute or relative path.)

`PATH_PAPERS` is the path to the directory with the downloaded papers. (Only used in abstract extraction)

`PATH_ANTHOLOGY` is the path to the `xml` directory in the ACL Anthology. (Only used in abstract extraction)

`PATH_DATASET` is the path to the `.txt` file of the NLP Scholar dataset. 

`PATH_DATASET_EXPANDED` is the path to the `.txt` file of the expanded dataset or where it is supposed to be created.

## Commands
All commands are preceded with `cli`.

### Dataset related
WIP

### Counting
The command `count` prints the term frequency of the top k grams/tokens.
It also prints the top k tf-idf scores. Both are calculated using [sklearn](https://github.com/scikit-learn/scikit-learn).

The option `--ngrams <n>` specifies the n of the n-grams. The default is `1`.
To set the lower and upper bounds of n one can use e.g. `--ngrams 1,2`.

Example: `cli count 10 --ngrams 2` prints the 10 bigrams with the highest term frequency and also separately tf-idf score.

### Counts over time
The command `counts-time` plots the top k grams over a specified time.
It counts the term frequency per year and plots all tokens that were in a top k in one year or more.
The time can be specified using the filters mentioned further down.

The option `--ngrams <n>` specifies the n of the n-grams. The default is `1`.
To set the lower and upper bounds of n one can use e.g. `--ngrams 1,2`.

The option `--tfidf` plots the tf-idf scores instead of the term frequencies.

The option `--name <name>` or `-n <name>` allows to name the file the plot will be saved to.

Example: `cli counts-time 10 --min-year 2011` plots all unigrams that were in a top 10 from 2011 onwards.

### Scattertext
The command `scatter` uses the library [scattertext](https://github.com/JasonKessler/scattertext) to compare the term frequencies of specified 2 subsets with an interactive scatterplot.
The filters to specify the subsets are mentioned further down.

The option `--fast` uses the spacy model `en_core_web_sm` instead of `en_core_web_trf`.
It will be faster, but less accurate.
Some lemmas might be incorrect.

The option `--name <name>` or `-n` allows to name the file the plot will be saved to.

Example: `cli scatter --venues ACL --year 2019 --venues2 --year 2020` will plot the ACL papers from 2019 against those from 2020.

### Topic modelling training
The command `topic-train` will train a topic model using an LDA implementation in [gensim](https://github.com/RaRe-Technologies/gensim). 
The amount of topics can be freely chosen.
It will also create an interactive plot using [pyLDAvis](https://github.com/bmabey/pyLDAvis).

The option `--name <name>` or `-n` allows to name the model and the file the plot will be saved to.

Example: `cli topic 10 --min-year 2010` will create a topic model with 10 topics with all the data available from 2010 onwards.

### Topics over time
WIP

### Semantic analysis
WIP

## Filters

### Data

### Venues

### Time

### Authors

