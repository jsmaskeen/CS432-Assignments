#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$ROOT_DIR/backend/.env"

if [[ ! -f "$ENV_FILE" ]]; then
	echo "Error: backend/.env not found at $ENV_FILE"
	echo "Create backend/.env (for example by copying backend/.env.example) and set MYSQL_USER / MYSQL_PASSWORD."
	exit 1
fi

set -a
source "$ENV_FILE"
set +a

MYSQL_DB="${MYSQL_DATABASE:-cabSharing}"

if [[ -z "${MYSQL_USER:-}" ]]; then
	echo "Error: MYSQL_USER is not set in backend/.env"
	exit 1
fi

if [[ -z "${MYSQL_PASSWORD:-}" ]]; then
	echo "Error: MYSQL_PASSWORD is not set in backend/.env"
	exit 1
fi

export MYSQL_PWD="$MYSQL_PASSWORD"

mysql -u"$MYSQL_USER" -D "$MYSQL_DB" < "$ROOT_DIR/SQL-Dump/dump.sql"
mysql -u"$MYSQL_USER" -D "$MYSQL_DB" -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Auth_Credentials; SET FOREIGN_KEY_CHECKS=1;"