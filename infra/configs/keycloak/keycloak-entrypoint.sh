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
# - Managed infra config (clients, scopes, roles, authentication flows,
#   identity providers): Reconciled on every start by the keycloak-config-cli
#   one-shot service (keycloak-config in docker-compose) — not by this script.
#   This includes the Langfuse sysadmin gate (custom browser flow, deny
#   sub-flows, marker client scope, and the realm browserFlow binding).
# - Realm token and session lifespans: Applied via kcadm update after startup,
#   but only while a lifespan still holds the Keycloak default (30 min idle /
#   10 h max / 5 min access token) — the first-start-only realm import never
#   propagates them to existing deployments, while operator overrides made in
#   the admin console must survive.
# - Realm mail server: same rule as the lifespans — written only while the
#   realm still has no mail server (Keycloak's default is an empty smtpServer)
#   or the platform's server without a client id, and only once
#   KEYCLOAK_SMTP_TENANT_ID and KEYCLOAK_SMTP_CLIENT_ID are set.
# - SMTP client secret: written to Keycloak's file vault (tmpfs), which the
#   realm references as ${vault.smtp-client-secret}, so it never enters the
#   realm export or database.

set -euo pipefail

mkdir -p /opt/keycloak/data/import

VAULT_DIR=/opt/keycloak/vault
mkdir -p "$VAULT_DIR"
if [[ -n "${KEYCLOAK_SMTP_CLIENT_SECRET:-}" ]]; then
  printf '%s' "$KEYCLOAK_SMTP_CLIENT_SECRET" > "$VAULT_DIR/aihub_smtp-client-secret"
fi

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

KCADM=/opt/keycloak/bin/kcadm.sh

# Writes the realm mail server while the realm has none (Keycloak's default is
# an empty smtpServer), or while it holds the platform's server with an empty
# client id: tenant and client id are substituted once, so a realm first
# started without them would otherwise never pick them up. Any other mail
# server was set by an operator in the admin console and is kept.
apply_realm_mail_server_default() {
  if [[ -z "${KEYCLOAK_SMTP_TENANT_ID:-}" || -z "${KEYCLOAK_SMTP_CLIENT_ID:-}" ]]; then
    echo "KEYCLOAK_SMTP_TENANT_ID or KEYCLOAK_SMTP_CLIENT_ID is empty; leaving realm mail server unchanged."
    return
  fi

  local current
  # kcadm returns nested objects empty unless their fields are listed.
  if ! current=$($KCADM get realms/aihub --fields 'smtpServer(host,authTokenClientId)' 2> /dev/null); then
    echo "ERROR: Failed to read realm mail server; leaving unchanged."
    return
  fi
  local platform_host='"host"[[:space:]]*:[[:space:]]*"smtp\.office365\.com"'
  local empty_client_id='"authTokenClientId"[[:space:]]*:[[:space:]]*""'
  if [[ "$current" =~ \"host\" ]] && ! [[ "$current" =~ $platform_host && "$current" =~ $empty_client_id ]]; then
    echo "Realm mail server already configured; leaving unchanged."
    return
  fi

  local smtp_file=/tmp/aihub-smtp-server.json
  cat > "$smtp_file.template" << 'SMTP_EOF'
{ "smtpServer": {"auth": "true", "authTokenClientId": "$(env:KEYCLOAK_SMTP_CLIENT_ID)", "authTokenClientSecret": "${vault.smtp-client-secret}", "authTokenScope": "https://outlook.office365.com/.default", "authTokenUrl": "https://login.microsoftonline.com/$(env:KEYCLOAK_SMTP_TENANT_ID)/oauth2/v2.0/token", "authType": "token", "from": "noreply.ai-hub@bbv.ch", "fromDisplayName": "Swiss AI-Hub", "host": "smtp.office365.com", "port": "587", "ssl": "false", "starttls": "true", "user": "noreply.ai-hub@bbv.ch"} }
SMTP_EOF
  bash_envsubst "$smtp_file.template" > "$smtp_file"
  $KCADM update realms/aihub -f "$smtp_file" \
    && echo "Realm mail server applied." \
    || echo "ERROR: Failed to apply realm mail server."
  rm -f "$smtp_file" "$smtp_file.template"
}

# Post-startup configuration applied on every start: realm token and session
# lifespans via kcadm (the realm import only runs on first start, so existing
# deployments would otherwise never pick up lifespan changes and stay on
# Keycloak defaults of 30 min idle / 10 h max / 5 min access token). Each
# lifespan is only written while it still holds the Keycloak default — values
# customized by operators in the admin console are left untouched.
(
  echo "Waiting for Keycloak to be ready before applying post-startup configuration..."
  until $KCADM config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" > /dev/null 2>&1; do
    sleep 3
  done

  current_lifespans=$($KCADM get realms/aihub \
    --fields ssoSessionIdleTimeout,ssoSessionMaxLifespan,accessTokenLifespan 2> /dev/null)
  lifespan_updates=()
  if [[ "$current_lifespans" =~ \"ssoSessionIdleTimeout\"[[:space:]]*:[[:space:]]*1800([^0-9]|$) ]]; then
    lifespan_updates+=(-s ssoSessionIdleTimeout=432000)
  fi
  if [[ "$current_lifespans" =~ \"ssoSessionMaxLifespan\"[[:space:]]*:[[:space:]]*36000([^0-9]|$) ]]; then
    lifespan_updates+=(-s ssoSessionMaxLifespan=2592000)
  fi
  if [[ "$current_lifespans" =~ \"accessTokenLifespan\"[[:space:]]*:[[:space:]]*300([^0-9]|$) ]]; then
    lifespan_updates+=(-s accessTokenLifespan=3600)
  fi
  if [ ${#lifespan_updates[@]} -gt 0 ]; then
    $KCADM update realms/aihub "${lifespan_updates[@]}" \
      && echo "Realm token and session lifespans applied successfully." \
      || echo "ERROR: Failed to apply realm token and session lifespans."
  else
    echo "Realm token and session lifespans differ from Keycloak defaults; leaving unchanged."
  fi

  apply_realm_mail_server_default
) &

exec /opt/keycloak/bin/kc.sh "$@" --import-realm --vault=file --vault-dir="$VAULT_DIR"
