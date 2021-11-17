# Package **NLP-Land-crawler**

The NLP-Land-crawler provides information retrieval functionalities for [dblp](https://dblp.org/), extracting and pre-processing abstracts, and storing data to the [NLP-Land-backend](https://github.com/ag-gipp/NLP-Land-backend).

The package provides the following funcitonalities:

- Information retrieval of dblp for open-access publicaitons
- Abstract extraction of open-access publications
- Pre-processing of abstracts
- Storage of publications, venues, and authors as entities into a REST API backend

## Getting started

## How to use the package

```python
import nlpland

dblp_client = nlpland.clients.dblp.DBLPClient()
dataset = dblp_client.fetch_releases().get_diff(date=Date.today())
nlpland = nlpland.clients.backend.store(dataset, dry_run=True)
```

Analogously, the `nlpland.cli` provides command line functions to run from your bash.

## How to use the cli

The cli calls functions from the two clients from `nlpland.client.dblp` and `nlpland.client.backend`.

```console
cli run dblp --time 2010-2020
```

### DBLP access

### Backend access

## Contributing

## License
