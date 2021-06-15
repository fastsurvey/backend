FROM python:3.8

# read commit hash and branch name as build arguments
ARG commit_sha
ARG branch_name

LABEL maintainer="Felix Böhm <felix@felixboehm.dev>"
LABEL source="https://github.com/fastsurvey/backend"
LABEL commit_sha=${commit_sha}
LABEL branch_name=${branch_name}

ENV COMMIT_SHA=${commit_sha}
ENV BRANCH_NAME=${branch_name}
ENV POETRY_VERSION=1.1.6

RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

# install dependencies and remove poetry afterwards
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-ansi --no-interaction
RUN pip uninstall --yes poetry

EXPOSE 8000

COPY /app /app

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
