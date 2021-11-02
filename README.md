# NLPLand

<p align="center">
<a href="https://codecov.io/gh/ag-gipp/NLPLand"><img src="https://codecov.io/gh/ag-gipp/NLPLand/branch/main/graph/badge.svg?token=7CL6B5LNKP"/></a>    
<a href="https://github.com/ag-gipp/NLPLand/actions/workflows/release.yaml"><img alt="Actions Status" src="https://github.com/ag-gipp/NLPLand/actions/workflows/release.yaml/badge.svg">    
<a href="https://github.com/ag-gipp/NLPLand/actions/workflows/main.yml"><img alt="Actions Status" src="https://github.com/ag-gipp/NLPLand/actions/workflows/main.yml/badge.svg?branch=main">
<a href="https://github.com/ag-gipp/NLPLand/releases"><img alt="Actions Status" src="https://img.shields.io/github/v/release/ag-gipp/NLPLand?sort=semver"></a>
<a href="https://github.com/ag-gipp/NLPLand/blob/master/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

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
(Should poetry not be able to find a python 3.7 installation, specify the python path using `poetry env use <path>` to create a venv based on the given python version.)

If you were not already in a venv, execute `poetry shell` to activate the newly created one.
(If the command does not work, try to activate the venv manually or try another shell.)

### .env

You have to rename the file `empty.env` to `.env`. In this file you have to set your variables. (Hint: All path variables can be either an absolute or relative path.)

`PATH_PAPERS` is the path to the directory with the downloaded papers.
(Only used in abstract extraction)

`PATH_ANTHOLOGY` is the path to the `xml` [directory in the ACL Anthology](https://github.com/acl-org/acl-anthology/tree/master/data/xml).
(Only used in abstract extraction)

`PATH_DATASET` is the path to the `.txt` file of the NLP Scholar dataset.

`PATH_DATASET_EXPANDED` is the path to the `.txt` file of the expanded dataset or where it is supposed to be created.

## Code quality and checks

To maintain a consistent and well-tested repository, we use unit tests, linting, and typing checkers with GitHub actions. We use pytest for testing, pylint for linting, and pyright for typing.
Every time code gets pushed to our repository these checks are executed and have to fullfill certain requirements before you can merge the code to our master branch.

We also use naming conventions for branches, commits, and pull requests to leverage GitHub workflow automation and keep the repository clean.

In the following we will describe how to run checks locally and which naming conventions we use.

### Running test pipelines locally

To run the test pipeline locally, make sure to install act from [here](https://github.com/nektos/act).

To run the full check suite, execute:

```sh
act -P self-hosted=nektos/act-environments-ubuntu:18.04
```

To run a single check from the pipeline such as linting, execute:

```sh
act -j linting -P self-hosted=nektos/act-environments-ubuntu:18.04
```

### Repository and naming conventions

Each feature request, bug, enhancement, etc. has to be related to an issue. We have templates for bugs and features requests when you create an issue on GitHub.
An issue should be a closed component that can be implemented by one developer in 1 day. If the issue is larger than that, split it into smaller components.
To identify the issue, we use labels such as `bug` or `enhancement`.

To start a new branch, please use the naming convention `{issue_number}`\_`{short_issue_acronym}`. When you are done working on the branch, include the following text in the last commit message `fixes {issue_numer}`. Then create a pull request including the text `resolves {issue_number}`.

We group issues using a task list in another issue that has the `Epic` label. These issues are larger components that need to be developed.
Each issue with the `Epic` label has a task list with each element of the task list being a issue (e.g., this one [#47](https://github.com/ag-gipp/NLPLand/issues/47)).
Whenever a pull request with the above convention gets merged, the corresponding issue gets closed, and the task in the Epic gets checked.

To indicate whether the PR is a patch, minor, or major update, please use #patch, #minor, #major in the last commit message of the PR and in the PR description.
See [here](https://github.com/anothrNick/github-tag-action) for more information.

To build changelogs, each pull-request needs one of the labels "fix", "feature", or "test". See [here](https://github.com/mikepenz/release-changelog-builder-action) for more information.

`PATH_DATASET` is the path to the `.txt` file of the [NLP Scholar dataset](http://saifmohammad.com/WebPages/nlpscholar.html).

`PATH_DATASET_EXPANDED` is the path to the `.txt` file of the expanded dataset or where it is supposed to be created.

### Getting Started

To get started we recommend downloading the ACL Anthology XML files and the NLP Scholar dataset and enter their paths into the .env.
Then set `PATH_DATASET_EXPANDED` in the .env to a path of your choice.
Next, run `cli extract anth --original` to create an extended dataset.
You can find out more about the command in the documentation further down.
Now you should be able to run all implemented analyses.

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
Any filters applied will be ignored by this mode.
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

The following filters are applicable to all commands except the few ones under [Misc](#misc).
They will filter out rows that do not match the specified filters or mask certain attributes.
Different filters can be applied simultaneously.
The filters will then work additively, i.e. the more different filters are specified, the more restrictive the selection is.

### Data

The filter `--data <type>` allows selecting only specific parts of the data.
To do so it will mask all non-selected entries.
Combinations are possible, by listing multiple types (see the example).
In those cases the multiple types will be additive, so the more is listed, the less is masked.
The following types exist:

`all` selects everything and is the equivalent to applying no `data` filter at all.

`titles` selects the titles of the papers.

`abstracts` selects the abstracts of the papers.

`abstracts-anth` selects the abstracts that were extracted from the ACL Anthology XML files.

`abstracts-rule` selects the abstracts that were extracted from the papers using the rule-based system.

Example: `cli count 10 --data titles,abstracts-anth` will count all words in the titles and additionally all abstracts that were extracted from the XML files.

### Venues

The filter `--venues <name(s)>` allows to select a subset of data containing only papers from specific venues.
It is possible to select one or multiple venues (see the example).
The venue name must match the name in the dataset, not the name of the folder the papers are saved in, as some special characters had to be removed or replaced for the folder naming.

Example: `cli count 10 --venues ACL,EMNLP` will only count words from paper published in ACL and EMNLP.

### Years

To filter the year of publication there are 3 filters one can use.

`--year <year>` selects papers that were published in that year according to the ACL Anthology.
This filter will overwrite the other two, should they be applied at the same time.

`--min-year <year>` selects papers that were published in that year or later.

`--max-year <year>` selects papers that were published in that year or before.

Example: `cli count 10 --min-year 2018 --max-year 2020` will count all words from papers published in 2018, 2019 and 2020.

### Authors

To filter the authors there are two options.
The filters ignore casing, but otherwise it has to be an exact match.
In the NLP Scholar dataset nearly all authors are saved like `<lastname>, <firstname>`.

`--author <name>` selects the papers where the author is in the list of authors.

`--fauthor <name>` selects the papers where the author is the first author.

Example: `cli count 10 --author "manning, christopher"` will count all words from papers Christopher Manning worked on.
