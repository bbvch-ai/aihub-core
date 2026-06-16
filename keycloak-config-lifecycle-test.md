# Keycloak config lifecycle — local test

Verify how the two Keycloak configuration lifecycles behave on an **already-initialized** deployment:

- **Managed** config (`keycloak/managed/*`) is reconciled by the `keycloak-config` service (keycloak-config-cli) on
  **every** container start — this is what an AI-Hub version upgrade updates.
- **Bootstrap** config (`keycloak/bootstrap/*`) is applied only by `--import-realm` on the **first** start. On an
  existing realm it is NOT re-applied (admin-console / operator edits survive).

This test changes one field of each kind and shows the managed change lands while the bootstrap change does not.

> Run every command from the repo root. `.env` must exist (`cp .env.dev .env` if missing). The shorthand
> `DC="docker compose -f infra/docker-compose.dev.yml --env-file .env"` is re-declared in each block so the blocks are
> independently copy-pasteable.

## 1. Start the stack

```bash
DC="docker compose -f infra/docker-compose.dev.yml --env-file .env"
$DC up -d --build
# wait until keycloak is healthy and the one-shot reconciler has exited 0:
$DC ps keycloak keycloak-config
$DC logs --tail 30 keycloak-config   # should show import lines then a clean finish
```

## 2. Record the baseline in the admin console

Open **http://localhost:8180** → log in `admin` / `admin` → switch to the **`aihub`** realm (top-left realm picker).

- **Managed subject** — *Realm roles → `AIHubSysAdmin` → Description*:
  `System administrator access to infrastructure tools (Dagster, SeaweedFS, Attu, etc.)`
- **Bootstrap subject** — *Realm settings → General → Display name*: `Swiss AI-Hub`

## 3. Make one edit of each kind, then regenerate

Edit the **templates** (not the generated files):

- Managed — `infra/deployment/templates/configs/keycloak/managed/10-roles.json.j2`: append ` [MANAGED EDIT]` inside the
  `AIHubSysAdmin` `"description"` string.
- Bootstrap — `infra/deployment/templates/configs/keycloak/bootstrap/realm-settings.json.j2`: change
  `"displayName": "Swiss AI-Hub"` to `"displayName": "Swiss AI-Hub [BOOTSTRAP EDIT]"`.

Convenience one-liners:

```bash
sed -i 's/Attu, etc.)"/Attu, etc.) [MANAGED EDIT]"/' \
  infra/deployment/templates/configs/keycloak/managed/10-roles.json.j2
sed -i 's/"displayName": "Swiss AI-Hub"/"displayName": "Swiss AI-Hub [BOOTSTRAP EDIT]"/' \
  infra/deployment/templates/configs/keycloak/bootstrap/realm-settings.json.j2

make generate-compose
```

Confirm both edits reached the generated outputs:

```bash
grep -c "MANAGED EDIT"   infra/configs/keycloak/managed/10-roles.dev.json     # 1  (keycloak-config input)
grep -c "BOOTSTRAP EDIT" infra/configs/keycloak/aihub-realm.dev.json          # 1  (first-start import only)
grep -c "MANAGED EDIT"   infra/configs/keycloak/aihub-realm.dev.json          # 1  (merged file also carries it)
```

> The merged `aihub-realm.dev.json` contains BOTH edits, but it only feeds `--import-realm` — so on an existing realm it
> changes nothing. The managed change reaches the realm via `keycloak-config`, below.

## 4. Apply: restart Keycloak, then re-run the reconciler

```bash
DC="docker compose -f infra/docker-compose.dev.yml --env-file .env"

# Bootstrap path: re-reads the merged realm file, but --import-realm SKIPS the existing realm.
$DC restart keycloak
# wait for Keycloak to report healthy again before reconciling:
until $DC exec keycloak sh -c 'exec 3<>/dev/tcp/127.0.0.1/9000; echo ok' >/dev/null 2>&1; do sleep 3; done

# Managed path: re-run the one-shot reconciler against the running realm.
$DC up -d --force-recreate --no-deps keycloak-config
$DC logs --tail 30 keycloak-config
```

## 5. Verify

Refresh the admin console (re-login if the session dropped during the Keycloak restart), realm `aihub`:

- ✅ **Managed change applied** — *Realm roles → `AIHubSysAdmin` → Description* now ends with `[MANAGED EDIT]`.
- ✅ **Bootstrap change NOT applied** — *Realm settings → General → Display name* is still `Swiss AI-Hub` (no
  `[BOOTSTRAP EDIT]`).

That is the whole point: managed config tracks the files on every restart; bootstrap config is frozen after the first
import.

## 6. (Optional, destructive — local only) Prove the bootstrap change WOULD apply on a fresh realm

This drops only the `keycloak` database (the other dev databases are untouched), forcing a fresh `--import-realm`.

```bash
DC="docker compose -f infra/docker-compose.dev.yml --env-file .env"
$DC stop keycloak keycloak-config
$DC exec postgres psql -U admin -d postgres -c "DROP DATABASE keycloak WITH (FORCE);"
$DC exec postgres psql -U admin -d postgres -c "CREATE DATABASE keycloak;"
$DC up -d keycloak keycloak-config
```

Now *Realm settings → General → Display name* shows `Swiss AI-Hub [BOOTSTRAP EDIT]` — the bootstrap change reaches a
*freshly initialized* realm, confirming it was only ever a first-start seed.

## 7. Clean up

```bash
git checkout -- \
  infra/deployment/templates/configs/keycloak/managed/10-roles.json.j2 \
  infra/deployment/templates/configs/keycloak/bootstrap/realm-settings.json.j2
make generate-compose

DC="docker compose -f infra/docker-compose.dev.yml --env-file .env"
$DC up -d --force-recreate --no-deps keycloak-config   # restore the AIHubSysAdmin description
# The displayName is already back to "Swiss AI-Hub" unless you ran step 6; if you did, it is restored
# on the next fresh import, or set it manually in the admin console.
```

## Background

- Lifecycle model + upgrade implications: `docs/docs/6_code_deep_dive/2_keycloak_configuration/`
- Operator notes: `infra/deployment/CLAUDE.md` (Keycloak Realm Configuration)
- Decision record: `docs/arc42/decisions/2026_06_12_declarative_keycloak_realm_reconciliation.md`
