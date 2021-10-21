FROM python:3.8.5-slim

LABEL maintainer="Felix Böhm <felix@felixboehm.dev>"
LABEL source="https://github.com/fastsurvey/backend"

# install poetry
ENV POETRY_VERSION=1.1.11
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock /

# install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-ansi --no-interaction && \
    rm pyproject.toml poetry.lock

EXPOSE 8000

# read commit hash and branch name as build arguments
ARG commit_sha branch_name
LABEL commit_sha=${commit_sha} branch_name=${branch_name}
ENV COMMIT_SHA=${commit_sha} BRANCH_NAME=${branch_name}

COPY /app /app

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
