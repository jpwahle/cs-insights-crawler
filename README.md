# cs-insights-crawler

<p align="center">
<a href="https://github.com/gipplab/cs-insights-crawler/actions/workflows/release.yml"><img alt="Actions Status" src="https://github.com/gipplab/NLPLand/actions/workflows/release.yaml/badge.svg">    
<a href="https://github.com/gipplab/cs-insights-crawler/actions/workflows/main.yml"><img alt="Actions Status" src="https://github.com/gipplab/NLPLand/actions/workflows/main.yml/badge.svg?branch=main">
<a href="https://github.com/gipplab/cs-insights-crawler/releases"><img alt="Actions Status" src="https://img.shields.io/github/v/release/gipplab/cs-insights-crawler?sort=semver"></a>
<a href="https://github.com/gipplab/cs-insights-crawler/blob/master/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

> This is the official crawler implementation for the [d3 dataset](https://github.com/gipplab/d3-dataset) in almost pure python. The crawler is also used for the [cs-insights project](https://github.com/gipplab/cs-insights-main).

> Starting from version 1.0.0, this project is using [semantic versioning](https://semver.org/), and supports [SemanticScholar](https://semanticscholar.org). For more info about the features supported, see the [releases](https://github.com/gipplab/cs-insights-crawler/releases).


## Installation & Setup

First install the package manager [poetry](https://python-poetry.org/):

```console
pip install poetry
```

Then run:

```console
poetry install
```

To start the crawling process, run:

```console
poetry run cli main --s2_use_papers --s2_use_abstracts --s2_filter_acl
```

For help run:

```console
poetry run cli main --help
```

## Code quality and tests

To maintain a consistent and well-tested repository, we use unit tests, linting, and typing checkers with GitHub actions. We use pytest for testing, pylint for linting, and pyright for typing.
Every time code gets pushed to our repository these checks are executed and have to fullfill certain requirements before you can merge the code to our master branch.

Whenever you create a pull request against the default branch, GitHub actions will create a CI job executing unit tests and linting.

To run all tests that are tested during CI locally, run:

```console
poetry run poe alltest
```

## Contributing

Fork the repo, make changes and send a PR. We'll review it together!

## License

This project is licensed under the terms of MIT license. For more information, please see the [LICENSE](LICENSE) file.

## Citation

If you use this repository, or use our tool for analysis, please cite our work:

## Citation
If you use this repository, or use our tool for analysis, please cite our work:

```bib
@inproceedings{Wahle2022c,
  title        = {D3: A Massive Dataset of Scholarly Metadata for Analyzing the State of Computer Science Research},
  author       = {Wahle, Jan Philip and Ruas, Terry and Mohammad, Saif M. and Gipp, Bela},
  year         = {2022},
  month        = {July},
  booktitle    = {Proceedings of The 13th Language Resources and Evaluation Conference},
  publisher    = {European Language Resources Association},
  address      = {Marseille, France},
  doi          = {},
}
```

Also make sure to cite the following papers if you use SemanticScholar data:

```bib
@inproceedings{ammar-etal-2018-construction,
    title = "Construction of the Literature Graph in Semantic Scholar",
    author = "Ammar, Waleed  and
      Groeneveld, Dirk  and
      Bhagavatula, Chandra  and
      Beltagy, Iz",
    booktitle = "Proceedings of the 2018 Conference of the North {A}merican Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 3 (Industry Papers)",
    month = jun,
    year = "2018",
    address = "New Orleans - Louisiana",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/N18-3011",
    doi = "10.18653/v1/N18-3011",
    pages = "84--91",
}
```

```bib
@inproceedings{lo-wang-2020-s2orc,
    title = "{S}2{ORC}: The Semantic Scholar Open Research Corpus",
    author = "Lo, Kyle  and Wang, Lucy Lu  and Neumann, Mark  and Kinney, Rodney  and Weld, Daniel",
    booktitle = "Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics",
    month = jul,
    year = "2020",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/2020.acl-main.447",
    doi = "10.18653/v1/2020.acl-main.447",
    pages = "4969--4983"
}
```

