#!/usr/bin/env bash

# export environment variables
export $(grep -v '^#' .env | xargs)
# run tests via pytest
poetry run pytest -sx --cov=app --cov-report=term-missing tests
