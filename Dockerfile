FROM python:3.8

WORKDIR /cs-insights-crawler
COPY . /cs-insights-crawler

RUN apt-get update && apt-get install liblapack-dev libblas-dev gfortran python3-venv -y
RUN pip install poetry
RUN poetry install --no-dev

CMD [ "poetry", "run", "cli", "main", "--s2_use_papers", "--s2_use_abstracts", "--s2_use_authors", "--s2_filter_dblp" ]
