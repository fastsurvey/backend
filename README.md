# Fastsurvey Backend

[![Maintainability](https://api.codeclimate.com/v1/badges/5bf56497eaca37fe1635/maintainability)](https://codeclimate.com/repos/61675e535da22f01b70008b4/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/5bf56497eaca37fe1635/test_coverage)](https://codeclimate.com/repos/61675e535da22f01b70008b4/test_coverage)

**Landing Page:** [fastsurvey.de](https://fastsurvey.de/)</br>
**Project Documentation:** [docs.fastsurvey.de](https://docs.fastsurvey.de/)</br>
**API Documentation:** [api.fastsurvey.de/documentation/redoc](https://api.fastsurvey.de/documentation/redoc)

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
