#!/usr/bin/env bash
set -euo pipefail

required_vars=(
  ODC_DEFAULT_DB_HOSTNAME
  ODC_DEFAULT_DB_PORT
  ODC_DEFAULT_DB_DATABASE
  ODC_DEFAULT_DB_USERNAME
  ODC_DEFAULT_DB_PASSWORD
)

for v in "${required_vars[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "Missing env var: ${v}" >&2
    exit 1
  fi
done

mkdir -p "$(dirname "$DATACUBE_CONFIG_PATH")"

cat > "$DATACUBE_CONFIG_PATH" <<EOF
[default]
index_driver: postgis
db_hostname: ${ODC_DEFAULT_DB_HOSTNAME}
db_port: ${ODC_DEFAULT_DB_PORT}
db_database: ${ODC_DEFAULT_DB_DATABASE}
db_username: ${ODC_DEFAULT_DB_USERNAME}
db_password: ${ODC_DEFAULT_DB_PASSWORD}
EOF

exec "$@"
