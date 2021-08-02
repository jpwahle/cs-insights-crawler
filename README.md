# NLPLand

This repository is part of the project titled "NLPLand and its Secrets".
The project is within the scope of the Information Retrieval course at the Bergische University of Wuppertal in the summer semester of 2021.
The following project description should give a broad overview over the project, but is subject to change.

### Project Description
The ACL Anthology (AA) is the largest single repository of thousands of articles on Natural Language Processing (NLP) and Computational Linguistics (CL). It contains valuable metadata (e.g. venues, authors’ name, title) that can be used to better understand the field. NLP Scholar, uses this data to examine the literature to identify broad trends in productivity, focus, and impact. We want to extend this analysis to specific components in NLP publications.

## Installation & Setup
### poetry
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

`PATH_PAPERS` is the path to the directory with the downloaded papers.
(Only used in abstract extraction)

`PATH_ANTHOLOGY` is the path to the `xml` [directory in the ACL Anthology](https://github.com/acl-org/acl-anthology/tree/master/data/xml).
(Only used in abstract extraction)

`PATH_DATASET` is the path to the `.txt` file of the NLP Scholar dataset. 

`PATH_DATASET_EXPANDED` is the path to the `.txt` file of the expanded dataset or where it is supposed to be created.


## Commands
All commands are preceded with `cli`.

### Paper download
The command `download` downloads and saves the papers to your computer.
The papers will be structured as follows: `<year>/<venue-name>/<paper-id>.pdf`.
Some special characters in the venue name and paper id will be removed or replaced, because of folder name restrictions.

Example: `cli download --min-year 2015` will download all papers from 2015 onwards.

### Abstract extraction
The command `extract <mode>` adds the abstracts to the dataset.
There are two modes and multiple options:

The mode `anth` to extract from the XML files.
This will always overwrite abstracts extracted with the rule-based system.
(Preferred option, but not all papers have an abstract in the anthology)

The mode `rule` to use the rule-based system.
(There might be errors/noise)

The option `--overwrite-rule` to overwrite previously with the rule-based system extracted abstracts.
This has no effect for `mode = anth`.

The option `--original` will use the original dataset as basis and not an already expanded one.
Warning: This will overwrite everything once it saves.

Example: `cli extract rule --overwrite-rule` will add new abstracts and overwrite all abstracts previously extracted with the rule-based system.


### Counting
The command `count <k>` prints the term frequency of the top k grams/tokens.
It also prints the top k tf-idf scores. Both are calculated using [sklearn](https://github.com/scikit-learn/scikit-learn).

The option `--ngrams <n>` specifies the n of the n-grams. The default is `1`.
To set the lower and upper bounds of n one can use e.g. `--ngrams 1,2`.

Example: `cli count 10 --ngrams 2` prints the 10 bigrams with the highest term frequency and also separately tf-idf score.

### Counts over time
The command `counts-time <k>` plots the top k grams over a specified time.
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

### Topic model training
The command `topic-train <k>` will train a topic model with `k` topics using an LDA implementation in [gensim](https://github.com/RaRe-Technologies/gensim).
It will also create an interactive plot using [pyLDAvis](https://github.com/bmabey/pyLDAvis).

The option `--name <name>` or `-n` allows to name the model and the file the plot will be saved to.

Example: `cli topic 10 --min-year 2010` will create a topic model with 10 topics with all the data available from 2010 onwards.

### Topics over time
WIP

### Semantic analysis
WIP

### Misc
These commands are mostly for development purposes and improving the rule-based system.

The command `checkdataset` prints a lot of information about the dataset and performs various checks.
The option `--original` uses the original dataset without abstracts.
By default, the expanded version is used.

The command `checkencode` checks if there are encoding issues in the abstracts by checking if `�` is in any abstracts.
It will print the abstracts with one or more `�` and other information.

The command `checkpaper <paper-path>` prints the raw text of the paper specified.

The command `countabstractsanth` counts the amount abstracts and papers in the ACL Anthology based on the XML files.

## Filters
The following filters are applicable to all non-misc (and for now non-dataset related) commands.
They will filter out rows that do not match the specified filters or mask certain attributes.
Different filter can be applied simultaneously. The filters will then work additively, i.e. the more different filters are specified, the more restrictive the selection is.

### Data
The filter `--data <type>` allows selecting only specific parts of the data.
To do so it will mask all non-selected entries.
Combinations are possible, by listing multiple types (see the example).
In those cases the multiple types will be additive, so the more is listed, the less is masked.
The following types exist:

`all` selects everything and is the equivalent to applying no `data` filter at all. 

`titles` selects the titles of the papers.

`abstracts` selects the abstracts of the papers.

`abstracts-anth` selects the abstracts that were extracted from the ACl Anthology XML files.

`abstracts-rule` selects the abstracts that were extracted from the papers using the rule-based system.

Example: `cli count 10 --data titles,abstracts-anth` will count all words in the titles and additionally all abstracts that were extracted from the XML files.

### Venues
The filter `--venues <name(s)>` allows to select a subset of data containing only papers from specific venues.
It is possible to select one or multiple venues (see the example).
The venue name must match the name in the dataset, not the name of the folder the papers are saved in, as some special characters had to be removed or replaced for the folder naming.

Example: `cli count 10 --venues ACL,EMNLP` will only count words from paper published in ACL and EMNLP.

### Years
To filter the year of publication there are 3 filters one can use.

`--year <year>` will only select papers that were published in that year according to the ACl Anthology.
This filter will overwrite the other two, should they be applied at the same time.

`--min-year <year>` will only select papers that were published in that year or later.

`--max-year <year>` will only select papers that were published in that year or before.

Example: `cli count 10 --min-year 2018 --max-year 2020` will count all words from papers published in 2018, 2019 and 2020.

### Authors
To filter the authors there are two options.
The filters ignore casing, but otherwise it has to be an exact match.
In the NLP Scholar dataset nearly all authors are saved like `<lastname>, <firstname>`.

`--author <name>` selects only the papers where the author is in the list of authors.

`--fauthor <name>` selects only the papers where the author is the first author.

Example: `cli count 10 --author "manning, christopher"` will count all words from papers Christopher Manning worked on.
