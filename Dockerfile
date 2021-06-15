FROM python:3.8

ARG COMMIT
ARG BRANCH

LABEL maintainer="Felix Böhm <felix@felixboehm.dev>"
LABEL source="https://github.com/fastsurvey/backend"

ENV COMMIT=${COMMIT}
ENV BRANCH=${BRANCH}

RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml pyproject.toml
RUN poetry install --no-dev

EXPOSE 8000

COPY /app /app

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
