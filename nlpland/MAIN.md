The NLP-Land-crawler provides information retrieval functionalities for [dblp](https://dblp.org/), extracting and pre-processing abstracts, and storing data to the [NLP-Land-backend](https://github.com/ag-gipp/NLP-Land-backend).

The package provides the following funcitonalities:

- Information retrieval of dblp for open-access publicaitons
- Abstract extraction of pdf files
- Storage of publications, venues, and authors as entities into a REST API backend

## How to use the cli

The cli can start crawling processes and store the the results in the backend.

```console
python -m nlpland.cli continous --overwrite_pdf_cache_dir --verbose
```

For help see:

```console
python -m nlpland.cli -h
```

## How to use the package

The package provides clients for DBLP, GROBID, and the NLP-Land-backend, a document crawler, and a transformer for schemas. In the following there is a minimal example on how they can be used.

```python
from datetime import datetime
from nlpland.client import DBLPClient, BackendClient, GrobidClient
from nlpland.crawl import DocumentCrawler
from nlpland.transform import Transformer

# Init some clients
dblp_client = client.DBLPClient()
backend_client = client.BackendClient(base_url="localhost:8000")
grobid_client = client.GrobidClient(base_url="localhost:8080")

# Get list of dblp release entities that were modified in the last 60 days
entites = dblp_client.download_and_filter_release(
    from_timestamp=datetime.today() - datetime.timedelta(days=60)
)

dataset = Transformer.convert_to_schema(
    entities=entites,
    author_schema=AuthorSchema,
    affiliation_schema=AffiliationSchema,
    publication_schema=PublicationSchema,
    venue_schema=VenueSchema,
)

nlpland = backend_client.store(dataset, dry_run=True)
```

Analogously, the `nlpland.cli` provides command line functions to run from your bash.

### DBLP access

### Backend access

## Contributing

## License
