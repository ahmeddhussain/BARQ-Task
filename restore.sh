#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="backups"

LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/*.dump 2>/dev/null | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
    echo -e "\033[91mERROR: No backup files found in ${BACKUP_DIR}/\033[0m"
    exit 1
fi

echo "Restoring from $LATEST_BACKUP..."

echo "Clearing existing data..."
docker exec -i postgres psql -U barq_app -d barq_tasks -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "Running pg_restore..."
docker exec -i postgres pg_restore -U barq_app -d barq_tasks -1 < "$LATEST_BACKUP"

echo -e "\n\033[92mSUCCESS: Database restored.\033[0m"