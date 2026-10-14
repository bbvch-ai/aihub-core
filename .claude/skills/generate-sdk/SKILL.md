---
name: generate-sdk
description: Regenerate the frontend TypeScript API client from the OpenAPI spec using openapi-ts. Verifies API server is running, runs the code generator against openapi-ts.config.ts, and lints the output into sdk/client/. Use when user says 'regenerate SDK', 'update API client', 'sync frontend types', 'generate TypeScript client', 'API changed, update frontend', or 'openapi-ts'. Do NOT use for scaffolding frontend pages or composables (use scaffold-frontend-page, scaffold-composable), backend API endpoint creation (use scaffold-api-endpoint), or manual SDK file edits (sdk/client/ is fully generated).
allowed-tools: Bash, Read, Grep, Glob, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Frontend API SDK Generation

Regenerate the TypeScript API client from the live OpenAPI specification.

## Step 1: Verify API Server Is Running

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/openapi.json
```

- **200**: Proceed to Step 2
- **Any other code or connection refused**: Stop and display this message:
  > API server not running at http://localhost:8000. Start it with:
  >
  > - `make run-dev` in `packages/api/` (the API is not part of `infra/docker-compose.dev.yml`)

### Stop every agent runner first

The API registers an endpoint pair per **discovered** agent class, so the spec depends on which runners happen to be
attached. Regenerating with a local agent running bakes that agent into the shared client — a RAG agent alone adds four
`…ToRAGAgent…` endpoints plus the `ChatMessage_Input/Output` and `*Block_Input/Output` schemas they pull in, roughly
2,900 lines of diff that belong to nobody's change. The committed SDK carries **no** agent-specific endpoints, which is
the baseline to reproduce.

```bash
pkill -f "app/.*_agent/main.py"
curl -s -H "Authorization: Bearer $SUPERUSER_TOKEN" http://localhost:8000/api/v1/openapi.json | grep -c "RagAgent"
```

Expect `0` before generating. Restart the runners afterwards.

## Step 2: Generate the SDK

Run from `packages/web/`:

```bash
cd packages/web && pnpm generate-sdk
```

This uses the config at `packages/web/openapi-ts.config.ts` to fetch the OpenAPI spec from
`http://localhost:8000/api/v1/openapi.json` and regenerate TypeScript files into `packages/web/sdk/client/`
(`types.gen.ts`, `sdk.gen.ts`, `schemas.gen.ts`, `client.gen.ts`, `transformers.gen.ts`). The admin plane
(`packages/sysadmin-web`, backend `packages/sysadmin-api` on :8001) has its own client; a `packages/core` change affects
both. To reproduce CI without a running stack use `/verify-sdk-sync`.

## Step 3: Do Not Lint the Output

`eslint.config.js` globally ignores `sdk/**` and the generator already runs prettier (`postProcess`), so `pnpm lint`
over the output is a no-op. Commit the files exactly as generated.

## Step 4: Verify and Report

1. Confirm generated files exist and are non-empty:

```bash
ls -la packages/web/sdk/client/types.gen.ts packages/web/sdk/client/sdk.gen.ts
```

2. Check for TypeScript compilation errors in the generated output:

```bash
cd packages/web && pnpm nuxi typecheck 2>&1 | head -30
```

3. Report what changed:

```bash
git diff --stat -- packages/web/sdk/client/
```

Summarize: new endpoints added, modified request/response types, removed endpoints, number of files changed.

## Examples

- `/generate-sdk` — Full regeneration workflow (verify, generate, lint, report)

## Troubleshooting

- **API not running**: Start it with `make run-dev` in `packages/api/`
- **pnpm not found**: Run `corepack enable` or install pnpm globally
- **Generation produces no changes**: The API spec may not have changed. Verify your API changes are deployed to the
  running server.

## When to Run

Run this skill after any of these changes:

- Adding new API endpoints (new routes in FastAPI)
- Modifying DTOs or Pydantic response/request models
- Changing route paths or HTTP methods
- Updating query parameters or path parameters
