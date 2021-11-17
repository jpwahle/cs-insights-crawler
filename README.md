# NLPLand

<p align="center">
<a href="https://codecov.io/gh/ag-gipp/NLPLand"><img src="https://codecov.io/gh/ag-gipp/NLPLand/branch/main/graph/badge.svg?token=7CL6B5LNKP"/></a>    
<a href="https://github.com/ag-gipp/NLPLand/actions/workflows/release.yaml"><img alt="Actions Status" src="https://github.com/ag-gipp/NLPLand/actions/workflows/release.yaml/badge.svg">    
<a href="https://github.com/ag-gipp/NLPLand/actions/workflows/main.yml"><img alt="Actions Status" src="https://github.com/ag-gipp/NLPLand/actions/workflows/main.yml/badge.svg?branch=main">
<a href="https://github.com/ag-gipp/NLPLand/releases"><img alt="Actions Status" src="https://img.shields.io/github/v/release/ag-gipp/NLPLand?sort=semver"></a>
<a href="https://github.com/ag-gipp/NLPLand/blob/master/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

## Installation & Setup

### poetry

First download poetry as explained [here](https://python-poetry.org/docs/#installation) or run

```console
pip install poetry
```

Then install dependencies with

```console
poetry install
```

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

### CI

To run the CI pipeline locally, make sure to install act from [here](https://github.com/nektos/act).

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

We group issues using a task list in another issue that has the `Epic` label. These issues are larger components that need to be developed.
Each issue with the `Epic` label has a task list with each element of the task list being a issue (e.g., this one [#47](https://github.com/ag-gipp/NLPLand/issues/47)).
Whenever a pull request with the above convention gets merged, the corresponding issue gets closed, and the task in the Epic gets checked.

When a branch is assigned to you, a new issue will be created from the `dev` branch including the issue number.

To indicate whether the PR is a patch, minor, or major update, please use #patch, #minor, #major in the last commit message of the PR and in the PR description.
See [here](https://github.com/anothrNick/github-tag-action) for more information.

To build changelogs, each pull-request needs one of the labels "fix", "feature", or "test". See [here](https://github.com/mikepenz/release-changelog-builder-action) for more information.

## Contributing

Fork the repo, make changes and send a PR. We'll review it together!

## License

This project is licensed under the terms of MIT license. For more information, please see the [LICENSE](LICENSE) file.

## Citation

If you use this repository, or use our tool for analysis, please cite our work:

TODO: Add citation here and as CITATION.cff file when paper is out.
