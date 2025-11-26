#!/usr/bin/env bash

set -e

echo "Initializing database schema..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < /docker-entrypoint-initdb.d/schema.sql

echo "Database initialized successfully"
