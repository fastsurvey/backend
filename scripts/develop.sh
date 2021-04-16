#!/bin/sh

uvicorn --port 8000 --host 0.0.0.0 app.main:app --reload --log-level debug --env-file .env