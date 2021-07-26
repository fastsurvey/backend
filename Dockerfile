FROM python:3.8

LABEL maintainer="Felix Böhm <felix@felixboehm.dev>"
LABEL source="https://github.com/fastsurvey/backend"

RUN pip install --upgrade pip && pip install poetry==1.1.6

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

# install dependencies and remove poetry afterwards
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-ansi --no-interaction && \
    pip uninstall --yes poetry && \
    rm pyproject.toml poetry.lock

EXPOSE 8000

# read commit hash and branch name as build arguments
ARG commit_sha
ARG branch_name

LABEL commit_sha=${commit_sha}
LABEL branch_name=${branch_name}

ENV COMMIT_SHA=${commit_sha}
ENV BRANCH_NAME=${branch_name}

COPY /app /app

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
