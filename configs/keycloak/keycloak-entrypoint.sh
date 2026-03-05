#!/bin/bash
# Keycloak entrypoint for all stages.
# Substitutes environment variables in realm JSON templates before import,
# applies identity providers via partialImport after startup, then starts Keycloak.
#
# Usage: keycloak-entrypoint.sh <kc.sh args...>
#   Dev:  keycloak-entrypoint.sh start-dev
#   Prod: keycloak-entrypoint.sh start --hostname=... --proxy-headers=...
#
# Keycloak's --import-realm does not support env var substitution natively,
# so we pre-process the template files with a pure-bash envsubst
# (the Keycloak image has no envsubst/perl/awk).
#
# Import strategy:
# - aihub-realm.json: Imported via --import-realm (creates realm on first start only)
# - identity-providers.json: Applied via partialImport API after startup (every start,
#   with OVERWRITE so config changes are picked up). This keeps the files separate
#   and avoids --import-realm's OVERWRITE_EXISTING destroying the realm.

set -euo pipefail

mkdir -p /opt/keycloak/data/import

bash_envsubst() {
  local content
  content=$(cat "$1")
  while IFS= read -r var; do
    if [[ -v $var ]]; then
      content=${content//"\${$var}"/"${!var}"}
    fi
  done < <(compgen -v)
  echo "$content"
}

for f in /opt/keycloak/data/import-templates/*.json; do
  bash_envsubst "$f" > "/tmp/$(basename "$f")"
done

# Only the realm file goes to --import-realm (first-start creation)
cp /tmp/aihub-realm.json /opt/keycloak/data/import/

# Apply identity providers via partialImport after Keycloak is ready
if [ -f /tmp/identity-providers.json ]; then
  (
    echo "Waiting for Keycloak to be ready before applying identity providers..."
    until /opt/keycloak/bin/kcadm.sh config credentials \
      --server http://localhost:8080 \
      --realm master \
      --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
      --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" > /dev/null 2>&1; do
      sleep 3
    done
    /opt/keycloak/bin/kcadm.sh create partialImport -r aihub \
      -s ifResourceExists=OVERWRITE \
      -f /tmp/identity-providers.json \
      && echo "Identity providers applied successfully." \
      || echo "ERROR: Failed to apply identity providers."
  ) &
fi

exec /opt/keycloak/bin/kc.sh "$@" --import-realm
