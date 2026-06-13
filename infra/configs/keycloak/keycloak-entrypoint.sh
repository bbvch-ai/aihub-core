#!/bin/bash
# Keycloak entrypoint for all stages.
# Substitutes environment variables in the realm JSON template before import,
# then starts Keycloak.
#
# Usage: keycloak-entrypoint.sh <kc.sh args...>
#   Dev:  keycloak-entrypoint.sh start-dev
#   Prod: keycloak-entrypoint.sh start --hostname=... --proxy-headers=...
#
# Keycloak's --import-realm does not support env var substitution natively,
# so we pre-process the template file with a pure-bash envsubst
# (the Keycloak image has no envsubst/perl/awk). Placeholders use the
# keycloak-config-cli syntax so all realm config files share one convention:
#   $(env:VAR)       — replaced with the env value (inside JSON strings)
#   "$(envjson:VAR)" — replaced including the quotes with the raw env value
#                      (used to inject JSON arrays like SUPERUSER_ROLES_JSON)
#
# Realm configuration mechanisms (see ADR 2026_06_12):
# - aihub-realm.json: Imported via --import-realm (creates realm on first
#   start only; existing realms are skipped by Keycloak's design).
# - Managed infra config (clients, scopes, roles, flows, identity providers):
#   Reconciled on every start by the keycloak-config-cli one-shot service
#   (keycloak-config in docker-compose) — not by this script.
# - Realm session lifespans: Applied via kcadm update after startup, but only
#   while a lifespan still holds the Keycloak default (30 min idle / 10 h max) —
#   the first-start-only realm import never propagates them to existing
#   deployments, while operator overrides made in the admin console must survive.

set -euo pipefail

mkdir -p /opt/keycloak/data/import

bash_envsubst() {
  local content
  content=$(cat "$1")
  while IFS= read -r var; do
    if [[ -v $var ]]; then
      content=${content//"\$(env:$var)"/"${!var}"}
      content=${content//"\"\$(envjson:$var)\""/"${!var}"}
    fi
  done < <(compgen -v)
  echo "$content"
}

bash_envsubst /opt/keycloak/data/import-templates/aihub-realm.json \
  > /opt/keycloak/data/import/aihub-realm.json

# Post-startup configuration applied on every start: realm session lifespans
# via kcadm (the realm import only runs on first start, so existing deployments
# would otherwise never pick up lifespan changes and stay on Keycloak defaults
# of 30 min idle / 10 h max). Each lifespan is only written while it still
# holds the Keycloak default — values customized by operators in the admin
# console are left untouched.
(
  echo "Waiting for Keycloak to be ready before applying post-startup configuration..."
  until /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" > /dev/null 2>&1; do
    sleep 3
  done
  current_lifespans=$(/opt/keycloak/bin/kcadm.sh get realms/aihub \
    --fields ssoSessionIdleTimeout,ssoSessionMaxLifespan 2> /dev/null)
  lifespan_updates=()
  if [[ "$current_lifespans" =~ \"ssoSessionIdleTimeout\"[[:space:]]*:[[:space:]]*1800([^0-9]|$) ]]; then
    lifespan_updates+=(-s ssoSessionIdleTimeout=432000)
  fi
  if [[ "$current_lifespans" =~ \"ssoSessionMaxLifespan\"[[:space:]]*:[[:space:]]*36000([^0-9]|$) ]]; then
    lifespan_updates+=(-s ssoSessionMaxLifespan=2592000)
  fi
  if [ ${#lifespan_updates[@]} -gt 0 ]; then
    /opt/keycloak/bin/kcadm.sh update realms/aihub "${lifespan_updates[@]}" \
      && echo "Realm session lifespans applied successfully." \
      || echo "ERROR: Failed to apply realm session lifespans."
  else
    echo "Realm session lifespans differ from Keycloak defaults; leaving unchanged."
  fi
) &

exec /opt/keycloak/bin/kc.sh "$@" --import-realm
