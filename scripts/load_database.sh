#!/usr/bin/env bash
# Start PostgreSQL in Docker and load telecom.sql into the tellco database.
#
# Usage (from project root):
#   chmod +x scripts/load_database.sh
#   ./scripts/load_database.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CONTAINER="tellco-postgres"
DB_NAME="tellco"
SQL_FILE="telecom.sql"

echo "==> Starting PostgreSQL container..."
docker compose up -d

echo "==> Waiting for PostgreSQL to be ready..."
until docker compose exec -T postgres pg_isready -U postgres -d "$DB_NAME" >/dev/null 2>&1; do
  sleep 2
done

ROW_COUNT="$(
  docker compose exec -T postgres psql -U postgres -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'xdr_data';" \
    | tr -d '[:space:]'
)"

if [[ "$ROW_COUNT" == "1" ]]; then
  EXISTING_ROWS="$(
    docker compose exec -T postgres psql -U postgres -d "$DB_NAME" -tAc \
      "SELECT COUNT(*) FROM public.xdr_data;" \
      | tr -d '[:space:]'
  )"
  if [[ "$EXISTING_ROWS" -gt 0 ]]; then
    echo "==> Data already loaded ($EXISTING_ROWS rows in xdr_data). Skipping import."
    exit 0
  fi
fi

if [[ ! -f "$SQL_FILE" ]]; then
  echo "ERROR: $SQL_FILE not found in project root."
  exit 1
fi

echo "==> Loading $SQL_FILE (this may take a few minutes)..."
docker compose exec -T postgres psql -U postgres -d "$DB_NAME" -f - < "$SQL_FILE"

FINAL_COUNT="$(
  docker compose exec -T postgres psql -U postgres -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM public.xdr_data;" \
    | tr -d '[:space:]'
)"

echo "==> Done. xdr_data row count: $FINAL_COUNT"
