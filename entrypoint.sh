#! /usr/bin/env bash

export UVICORN_PORT="${UVICORN_PORT:-8000}"
export UVICORN_WORKERS="${UVICORN_WORKERS:-1}"

uvicorn hackathon.main:app --host "0.0.0.0" --port "${UVICORN_PORT}" --workers "${UVICORN_WORKERS}"