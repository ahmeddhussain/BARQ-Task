#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/barq_tasks_${TIMESTAMP}.dump"

echo "Creating backup directory..."
mkdir -p "$BACKUP_DIR"

echo "Running pg_dump inside the postgres container..."

docker exec -i postgres pg_dump -U barq_app -d barq_tasks -F c > "$BACKUP_FILE"

echo -e "\n\033[92mSUCCESS: Database backed up to ${BACKUP_FILE}\033[0m"