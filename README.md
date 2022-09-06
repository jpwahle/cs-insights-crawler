# cs-insights-crawler

<p align="center">
<a href="https://github.com/gipplab/cs-insights-crawler/actions/workflows/release.yaml"><img alt="Actions Status" src="https://github.com/gipplab/NLPLand/actions/workflows/release.yaml/badge.svg">    
<a href="https://github.com/gipplab/cs-insights-crawler/actions/workflows/main.yml"><img alt="Actions Status" src="https://github.com/gipplab/NLPLand/actions/workflows/main.yml/badge.svg?branch=main">
<a href="https://github.com/gipplab/cs-insights-crawler/releases"><img alt="Actions Status" src="https://img.shields.io/github/v/release/gipplab/cs-insights-crawler?sort=semver"></a>
<a href="https://github.com/gipplab/cs-insights-crawler/blob/master/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

## Installation & Setup

We are providing two ways to setup this project.

<details> <summary> Production </summary>
<br/>
In production mode an instance of the NLP-Land-backend and grobid server are created in Docker and the contionous crawling process of this repository is running.

To spin up the production version of this project, switch into the root directory of this project and run:

```console
docker-compose up --build
```

</details>

<details> <summary> Development </summary>
<br/>
If you want to actively develop this project, you need to install the project and dependencies locally.

First install the package manager [poetry](https://python-poetry.org/):

```console
pip install poetry
```

Then run:

```console
poetry install
```

Spin up an instance of GROBID with docker or follow the steps to run GROBID locally [here](https://grobid.readthedocs.io/en/latest/Install-Grobid/).

```console
docker run -t --init \
-p 8070:8070 \
-p 8071:8071 \
-v ./grobid.yaml:/opt/grobid/grobid-home/config/grobid.yaml
--name grobid \
lfoppiano/grobid:0.7.0
```

Although in production docker is used, it might make sense to run GROBID locally for performance reasons.

> Note: If you are using MacOS or Windows without WSL, local builds are highly recommended because translation to linux kernels is too slow and will cause timeouted requests.

> If you are using MacOS, it is recommended to use JDK 15 with Gradle 7.

Then you can run the cli which automatically connects to those services like this:

```console
poetry run cli main
```

For help run:

```console
poetry run cli main --help
```

</details>

## Code quality and tests

To maintain a consistent and well-tested repository, we use unit tests, linting, and typing checkers with GitHub actions. We use pytest for testing, pylint for linting, and pyright for typing.
Every time code gets pushed to our repository these checks are executed and have to fullfill certain requirements before you can merge the code to our master branch.

We also use naming conventions for branches, commits, and pull requests to leverage GitHub workflow automation and keep the repository clean.

In the following we will describe how to run checks locally and which naming conventions we use.

### CI

Whenever you create a pull request against the default branch, GitHub actions will create a CI job executing unit tests and linting.

### Replicate CI locally

<details> <summary> Recommended: Replicate GitHub action pipeline with Docker </summary>

If you want to replicate the exact same pipeline that runs on GitHub actions, install act from [here](https://github.com/nektos/act).

To run the full check suite, execute:

```sh
act -j Test
```

To run a single check from the pipeline such as linting, execute:

```sh
act -j Lint
```

</details>
<details> <summary> Not Recommended: run it locally on host OS </summary>

You can also run each of the commands checked in `.github/workflows/main.yml`:

```console
poetry run poe alltest
```

</details>

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
