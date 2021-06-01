# Fastsurvey Backend

[![Maintainability](https://api.codeclimate.com/v1/badges/0886890b76260c1eb047/maintainability)](https://codeclimate.com/github/fastsurvey/backend/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/0886890b76260c1eb047/test_coverage)](https://codeclimate.com/github/fastsurvey/backend/test_coverage)

**Project Documentation:** [docs.fastsurvey.io](https://docs.fastsurvey.io/)
**API Documentation:** [backend.dev.fastsurvey.io/documentation/redoc](https://backend.dev.fastsurvey.io/documentation/redoc)

---

## Security

We take security very seriously. If you believe you have discovered a vulnerability, privacy issue, exposed data, or other security issues in any of our assets, we want to hear from you. Please send an email to the maintainer at felix@felixboehm.dev.

## Running

- install dependencies via `poetry install --remove-untracked`
- specify your environment variables in a `.env` file
- run tests via `./scripts/test`
- run in development mode via `./scripts/develop`
- run with docker via `./scripts/build && ./scripts/run`
- the server is reachable under `localhost:8000`
