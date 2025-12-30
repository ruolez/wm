#!/bin/bash
poetry install --no-root --no-interaction --no-ansi
exec "$@"