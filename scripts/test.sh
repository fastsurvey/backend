#!/usr/bin/env bash

env $(grep -v '^#' .env | xargs) poetry run pytest -sx --cov=app --cov-report=term-missing tests
