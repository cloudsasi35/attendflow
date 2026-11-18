-- Creates or updates the read-only role that postgres-exporter uses to read statistics.
-- Idempotent: safe to run again after a password change.
-- Run as the Postgres superuser; the password is passed in as psql variable exporter_pw.
-- pg_monitor grants read access to the pg_stat_* views and nothing that writes data.
\set ON_ERROR_STOP on

SELECT format('CREATE ROLE attendflow_monitor LOGIN PASSWORD %L', :'exporter_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'attendflow_monitor') \gexec

SELECT format('ALTER ROLE attendflow_monitor LOGIN PASSWORD %L', :'exporter_pw') \gexec

GRANT pg_monitor TO attendflow_monitor;
