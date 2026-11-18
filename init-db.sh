#!/bin/bash
set -e

echo "Initializing AttendFlow database..."

# Create attendflow user and database
psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    CREATE USER attendflow WITH PASSWORD '${APP_DB_PASSWORD}' CREATEDB;
    CREATE DATABASE attendflow OWNER attendflow;
    \du
EOSQL

echo "Database initialization complete!"
