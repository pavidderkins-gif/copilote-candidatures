#!/usr/bin/env bash
# Lance les migrations Supabase sur un PostgreSQL local jetable, puis les tests.
# Usage : scripts/test-db.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PGBIN="${PGBIN:-$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)}"
TMP="$(mktemp -d)"
PORT="${PORT:-55432}"
trap '"$PGBIN/pg_ctl" -D "$TMP/data" -m immediate stop >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT

RUN=()
if [ "$(id -u)" = 0 ]; then
  chown -R postgres "$TMP"
  RUN=(runuser -u postgres --)
fi

"${RUN[@]}" "$PGBIN/initdb" -D "$TMP/data" -U postgres -A trust -E UTF8 --locale=C.UTF-8 >/dev/null
"${RUN[@]}" "$PGBIN/pg_ctl" -D "$TMP/data" -o "-p $PORT -k $TMP -c listen_addresses=''" -l "$TMP/log" -w start >/dev/null

PSQL=(psql -h "$TMP" -p "$PORT" -U postgres -v ON_ERROR_STOP=1 -q)
"${PSQL[@]}" -c "create database copilote" postgres

# Bouchons des objets fournis par Supabase (rôles, schéma storage)
"${PSQL[@]}" copilote <<'SQL'
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create schema storage;
create table storage.buckets (id text primary key, name text not null, public boolean default false);
create table storage.objects (id uuid primary key default gen_random_uuid(), bucket_id text references storage.buckets(id), name text);
alter table storage.objects enable row level security;
SQL

for f in "$ROOT"/supabase/migrations/*.sql; do
  echo "→ $(basename "$f")"
  "${PSQL[@]}" copilote -f "$f"
done

"${PSQL[@]}" copilote -f "$ROOT/supabase/tests/socle_test.sql"
