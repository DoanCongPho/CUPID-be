#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Poetry, then the locked dependencies.
# virtualenvs.create=false installs straight into the host's Python, so the
# start command does not need a `poetry run` prefix.
pip install poetry
poetry config virtualenvs.create false
poetry install

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
