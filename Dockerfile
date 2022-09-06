FROM node:17

RUN mkdir /crawler
WORKDIR /crawler
COPY ./ /crawler/

RUN poetry install --no-dev
RUN poetry run poe crawl