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
# - Langfuse sysadmin gate: Reconciled via kcadm after startup (every start), because
#   authentication flows are not supported by partialImport and the realm file is only
#   imported on first start. Each step checks for existence first, so already-initialized
#   instances converge to the same state as a fresh --import-realm.

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

KCADM=/opt/keycloak/bin/kcadm.sh

# Reads "id,<value>" csv lines (kcadm --format csv --noquotes) from stdin and
# prints the id of the line whose value matches $1.
kc_lookup_id() {
  local id value
  while IFS=, read -r id value; do
    if [ "$value" = "$1" ]; then
      echo "$id"
      return 0
    fi
  done
  return 1
}

# True if a TOP-LEVEL flow with alias $1 exists (sub-flows are not listed here).
kc_flow_exists() {
  local alias
  while IFS= read -r alias; do
    if [ "$alias" = "$1" ]; then
      return 0
    fi
  done < <($KCADM get authentication/flows -r aihub --fields alias --format csv --noquotes)
  return 1
}

# Prints the execution id whose displayName is $2 within flow $1 (alias, URL-encoded).
# For sub-flow executions the displayName equals the sub-flow alias.
kc_exec_id() {
  $KCADM get "authentication/flows/$1/executions" -r aihub \
    --fields id,displayName --format csv --noquotes | kc_lookup_id "$2"
}

# Adds an authenticator execution to flow $1 with requirement $3.
# $2 is the authenticator provider id. Prints the execution id.
add_execution() {
  local flow="$1" provider="$2" requirement="$3" exec_id
  $KCADM create "authentication/flows/$flow/executions/execution" -r aihub -s provider="$provider" > /dev/null || return 1
  exec_id=$($KCADM get "authentication/flows/$flow/executions" -r aihub \
    --fields id,providerId --format csv --noquotes | kc_lookup_id "$provider") || return 1
  $KCADM update "authentication/flows/$flow/executions" -r aihub -n \
    -b "{\"id\":\"$exec_id\",\"requirement\":\"$requirement\"}" || return 1
  echo "$exec_id"
}

# Adds sub-flow $2 to parent flow $1 (alias, URL-encoded) with requirement $3
# and description $4.
add_subflow() {
  local parent="$1" alias="$2" requirement="$3" description="$4" exec_id
  $KCADM create "authentication/flows/$parent/executions/flow" -r aihub \
    -b "{\"alias\":\"$alias\",\"type\":\"basic-flow\",\"description\":\"$description\"}" || return 1
  exec_id=$(kc_exec_id "$parent" "$alias") || return 1
  $KCADM update "authentication/flows/$parent/executions" -r aihub -n \
    -b "{\"id\":\"$exec_id\",\"requirement\":\"$requirement\"}" || return 1
}

# Adds an authenticator execution to sub-flow $1, promotes it to REQUIRED and
# attaches config $3. $2 is the authenticator provider id.
add_gate_execution() {
  local flow="$1" provider="$2" config="$3" exec_id
  exec_id=$(add_execution "$flow" "$provider" REQUIRED) || return 1
  $KCADM create "authentication/executions/$exec_id/config" -r aihub -b "$config" || return 1
}

# Builds the custom browser flow. The authentication alternatives are nested in
# a REQUIRED sub-flow because a CONDITIONAL sub-flow (the gate) at the same
# level as ALTERNATIVE executions would disable them.
create_browser_flow() {
  $KCADM create authentication/flows -r aihub \
    -s alias=browser-aihub -s providerId=basic-flow -s topLevel=true -s builtIn=false \
    -s 'description=Browser flow with a deny gate for clients carrying the langfuse-sysadmin-gate scope. Review on Keycloak major upgrades.' || return 1
  add_subflow browser-aihub browser-aihub-authenticate REQUIRED \
    "Authentication alternatives of the built-in browser flow, nested in a REQUIRED sub-flow so the CONDITIONAL gate does not disable them." || return 1
  add_execution browser-aihub-authenticate auth-cookie ALTERNATIVE > /dev/null || return 1
  add_execution browser-aihub-authenticate identity-provider-redirector ALTERNATIVE > /dev/null || return 1
  add_subflow browser-aihub-authenticate browser-aihub-forms ALTERNATIVE \
    "Username, password, otp and other auth forms." || return 1
  add_execution browser-aihub-forms auth-username-password-form REQUIRED > /dev/null || return 1
  add_subflow browser-aihub-forms browser-aihub-conditional-2fa CONDITIONAL \
    "Flow to determine if the OTP is required for the authentication." || return 1
  add_execution browser-aihub-conditional-2fa conditional-user-configured REQUIRED > /dev/null || return 1
  add_execution browser-aihub-conditional-2fa auth-otp-form ALTERNATIVE > /dev/null || return 1
}

# Creates the CONDITIONAL gate sub-flow $2 under parent flow $1 (alias, URL-encoded):
# deny access unless the user has AIHubSysAdmin, only for clients carrying the
# langfuse-sysadmin-gate scope. $3 is the prefix for the (realm-unique) config aliases.
add_gate_subflow() {
  local parent="$1" alias="$2" cfg="$3" exec_id
  $KCADM create "authentication/flows/$parent/executions/flow" -r aihub \
    -b "{\"alias\":\"$alias\",\"type\":\"basic-flow\",\"description\":\"Conditional sub-flow: deny clients carrying the langfuse-sysadmin-gate scope unless the user has the AIHubSysAdmin role\"}" || return 1
  exec_id=$(kc_exec_id "$parent" "$alias") || return 1
  $KCADM update "authentication/flows/$parent/executions" -r aihub -n \
    -b "{\"id\":\"$exec_id\",\"requirement\":\"CONDITIONAL\"}" || return 1
  add_gate_execution "$alias" conditional-client-scope \
    "{\"alias\":\"$cfg-scope-condition\",\"config\":{\"client_scope\":\"langfuse-sysadmin-gate\",\"negate\":\"false\"}}" || return 1
  add_gate_execution "$alias" conditional-user-role \
    "{\"alias\":\"$cfg-role-condition\",\"config\":{\"condUserRole\":\"AIHubSysAdmin\",\"negate\":\"true\"}}" || return 1
  add_gate_execution "$alias" deny-access-authenticator \
    "{\"alias\":\"$cfg-deny-message\",\"config\":{\"error_message\":\"Access denied. Langfuse is restricted to system administrators (AIHubSysAdmin). Please contact your administrator.\"}}" || return 1
}

# Reconciles the Langfuse sysadmin gate (see keycloak-realm.json.j2 for the
# declarative first-start equivalent). Idempotent: every step is skipped or a
# no-op when the resource already exists.
apply_langfuse_gate() {
  local post_broker_flow="Post%20Broker%20Login%20-%20AIHubAccess%20Check"
  local scope_id client_uid

  # 1. Marker client scope
  scope_id=$($KCADM get client-scopes -r aihub --fields id,name --format csv --noquotes | kc_lookup_id langfuse-sysadmin-gate) \
    || scope_id=$($KCADM create client-scopes -r aihub -i \
      -b '{"name":"langfuse-sysadmin-gate","description":"Marker scope (no mappers). Presence as a default client scope activates the AIHubSysAdmin deny gate in the authentication flows.","protocol":"openid-connect","attributes":{"include.in.token.scope":"false","display.on.consent.screen":"false"}}') || return 1

  # 2. Attach as default scope to the langfuse client (PUT is idempotent)
  client_uid=$($KCADM get clients -r aihub -q clientId=langfuse --fields id --format csv --noquotes) || return 1
  [ -n "$client_uid" ] || return 1
  $KCADM update "clients/$client_uid/default-client-scopes/$scope_id" -r aihub -n || return 1

  # 3. Custom browser flow (upgrade path for already-initialized instances;
  #    fresh imports get it from the realm file)
  kc_flow_exists browser-aihub || create_browser_flow || return 1

  # 4./5. Gate sub-flows in the browser and post-broker flows
  kc_exec_id browser-aihub langfuse-gate-browser > /dev/null \
    || add_gate_subflow browser-aihub langfuse-gate-browser langfuse-gate-browser || return 1
  kc_exec_id "$post_broker_flow" langfuse-gate-post-broker > /dev/null \
    || add_gate_subflow "$post_broker_flow" langfuse-gate-post-broker langfuse-gate-post-broker || return 1

  # 6. Bind the realm browser flow
  $KCADM update realms/aihub -s browserFlow=browser-aihub || return 1
}

# Apply identity providers and the Langfuse sysadmin gate after Keycloak is ready
(
  echo "Waiting for Keycloak to be ready before applying admin API config..."
  until $KCADM config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" > /dev/null 2>&1; do
    sleep 3
  done

  if [ -f /tmp/identity-providers.json ]; then
    $KCADM create partialImport -r aihub \
      -s ifResourceExists=OVERWRITE \
      -f /tmp/identity-providers.json \
      && echo "Identity providers applied successfully." \
      || echo "ERROR: Failed to apply identity providers."
  fi

  if apply_langfuse_gate; then
    echo "Langfuse sysadmin gate applied successfully."
  else
    echo "ERROR: Failed to apply Langfuse sysadmin gate."
  fi
) &

exec /opt/keycloak/bin/kc.sh "$@" --import-realm
