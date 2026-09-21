---
name: verify-sdk-sync
description: Check whether the committed frontend SDK client (packages/web/sdk/client, packages/sysadmin-web/sdk/client) still matches the backend OpenAPI spec, and regenerate it if not. Reproduces the Verify SDK Sync CI job offline -- no Docker stack, no running API. Run this BEFORE committing, pushing or opening a PR whenever the change touches packages/api/, packages/sysadmin-api/, packages/core/, either sdk/ directory, pnpm-lock.yaml or uv.lock -- including changes that look documentation-only, because Pydantic promotes a model's class docstring into its OpenAPI schema description. Use when user says 'Verify SDK Sync failed', 'SDK client is out of sync', 'check SDK drift', 'did I need to regenerate the SDK', or after editing any Pydantic event/DTO in packages/core. Do NOT use for a plain regeneration request with no drift question (use generate-sdk), scaffolding frontend code (use scaffold-composable, scaffold-frontend-page), or backend endpoint creation (use scaffold-api-endpoint).
allowed-tools: Bash, Read, Grep, Glob
---

# Verify SDK Sync

The committed TypeScript client must match what the backend OpenAPI spec generates. This skill answers one question --
*has it drifted?* -- and repairs it if so.

It is a guard, not a generator. For "just regenerate it, I know it changed", `/generate-sdk` is the simpler skill.

## Step 0: Does this change need the check?

Run the guard before anything else. It mirrors the CI workflow's own path filter.

```bash
BASE=$(git merge-base HEAD origin/main)
git diff --name-only "$BASE"...HEAD | grep -qE \
  "^(packages/(api|sysadmin-api|core)/|packages/(web|sysadmin-web)/sdk/|pnpm-lock\.yaml$|uv\.lock$)" \
  && echo "CHECK REQUIRED" || echo "no SDK-relevant change -- stop here"
```

On a `release/*` branch, substitute that branch for `origin/main`.

No match means the spec cannot have moved. Say so and stop — do not regenerate "just in case", since an unnecessary
regeneration on a stale environment produces a diff that belongs to nobody's change.

**Do not skip the check because the change looks documentation-only.** Pydantic promotes a model's class docstring to
its OpenAPI schema `description`. Editing a docstring on an event or DTO *is* a contract change and *does* alter
`schemas.gen.ts` and `types.gen.ts`. This is exactly how PR #1905 shipped drift.

## Step 1: Pick the plane

A `packages/core` change affects **both** planes — check each. Otherwise check only the one whose backend you touched.

| Frontend                | Backend                 | Port   | App module                       |
| ----------------------- | ----------------------- | ------ | -------------------------------- |
| `packages/web`          | `packages/api`          | `8000` | `app.main`                       |
| `packages/sysadmin-web` | `packages/sysadmin-api` | `8001` | `swiss_ai_hub.sysadmin_api.main` |

## Step 2: Export the spec offline

No services needed. The OpenAPI document is static, and connections live in the FastAPI lifespan, which never runs on
import. This is byte-for-byte what CI does, so what you commit is what CI regenerates.

Substitute the backend directory, port and app module for your plane.

```bash
cd packages/api                       # or packages/sysadmin-api
set -a; . ../../.env.dev; set +a      # import-time BaseSettings read the environment
export SPEC_DIR=/tmp/spec/api/v1 APP_MODULE=app.main
mkdir -p "$SPEC_DIR"
uv run python - <<'PY'
import json, os
from importlib import import_module
from fastapi import FastAPI
from starlette.routing import Mount
app = import_module(os.environ["APP_MODULE"]).app
mount = next(r for r in app.routes if isinstance(r, Mount) and isinstance(r.app, FastAPI))
schema = mount.app.openapi()
# The live server injects the mount path as the server URL from the request root_path.
# Offline there is no request, so replicate it or the generated client baseURL drifts.
schema["servers"] = [{"url": mount.path}]
with open(os.path.join(os.environ["SPEC_DIR"], "openapi.json"), "w") as handle:
    json.dump(schema, handle)
PY
```

## Step 3: Serve it and regenerate

Serving at the generator's own URL means `openapi-ts.config.ts` needs no edit.

```bash
python3 -m http.server 8000 --directory /tmp/spec &
curl -sf -o /dev/null http://localhost:8000/api/v1/openapi.json && echo "spec served"

cd packages/web && pnpm generate-sdk   # or packages/sysadmin-web

pkill -f "http.server 8000"
```

Always stop the server — a stray one on `:8000` shadows the real API later.

## Step 4: Read the diff

```bash
git diff --stat -- packages/web/sdk/client/
```

- **No diff** — in sync. Report that and stop.
- **Diff** — the committed client was stale. Commit the regenerated files exactly as produced.

Never hand-edit `sdk/client/`; it is fully generated, and CI diffs it byte for byte. A diff touching only `description`
strings and doc comments is still a real diff and still fails CI — commit it.

Do not run `pnpm lint` over the output. `eslint.config.js` globally ignores `sdk/**`, so it is a no-op; the generator's
`postProcess: ['prettier']` has already formatted the files.

Commit as its own change, e.g. `fix(<scope>): Regenerate web SDK client for <what moved>`.

## Why this skill exists

`.github/workflows/verify-sdk-sync.yml` regenerates both planes in CI and fails on any diff — but it triggers on
`pull_request: branches: [main]` **only**.

A PR targeting a `release/*` branch gets no such check. Drift merges there unnoticed and surfaces later on the
forward-port to `main`, in a PR whose author did not cause it. That is the #1905 → #1907 → #1912 chain: a docstring edit
merged to `release/0.321` unchecked, failed on the forward-port, and needed a separate repair PR against the release
branch.

**On a release branch, this skill is the only check there is.**

## Troubleshooting

| Problem                                     | Solution                                                                        |
| ------------------------------------------- | ------------------------------------------------------------------------------- |
| Import error during the export              | `uv sync --all-packages --dev` from the workspace root                          |
| `ValidationError` at import time            | `.env.dev` was not sourced — import-time `BaseSettings` read the environment    |
| Diff full of `…ToRAGAgent…` endpoints       | A real API server answered instead of the static file; confirm `:8000` is yours |
| `baseURL` differs from the committed client | The `schema["servers"]` line was dropped from the export script                 |
| CI still fails after a clean local run      | Check you regenerated the plane CI names, and pushed the commit CI tested       |

## Examples

- `/verify-sdk-sync` — run the guard; check and repair only if the diff warrants it
- `/verify-sdk-sync` after a red `Verify SDK Sync` job — reproduce CI locally and commit the fix
