# Fastsurvey Backend

[![Maintainability](https://api.codeclimate.com/v1/badges/0886890b76260c1eb047/maintainability)](https://codeclimate.com/github/fastsurvey/backend/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/0886890b76260c1eb047/test_coverage)](https://codeclimate.com/github/fastsurvey/backend/test_coverage)

**Project Documentation:** [docs.fastsurvey.de](https://docs.fastsurvey.de/)</br>
**API Documentation:** [api.dev.fastsurvey.de/documentation/redoc](https://api.dev.fastsurvey.de/documentation/redoc)

---

## Security

We take security very seriously. If you believe you have discovered a vulnerability, privacy issue, exposed data, or other security issues in any of our code, we want to hear from you. Please send an email to security@fastsurvey.de.

## Running

- specify your environment variables in a `.env` file
- build and run with docker via `./scripts/build && ./scripts/run`

## Development

- specify your environment variables in a `.env` file
- install dependencies via `poetry install --remove-untracked`
- run tests via `./scripts/test`
- run in development mode via `./scripts/develop`
