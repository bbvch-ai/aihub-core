---
name: generate-sdk
description: Regenerate the frontend TypeScript API client from the OpenAPI spec using openapi-ts. Verifies API server is running, runs the code generator against openapi-ts.config.ts, and lints the output into sdk/client/. Use when user says 'regenerate SDK', 'update API client', 'sync frontend types', 'generate TypeScript client', 'API changed, update frontend', or 'openapi-ts'. Do NOT use for scaffolding frontend pages or composables (use scaffold-frontend-page, scaffold-composable), backend API endpoint creation (use scaffold-api-endpoint), or manual SDK file edits (sdk/client/ is fully generated).
allowed-tools: Bash, Read, Grep, Glob, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Frontend API SDK Generation

Regenerate the TypeScript API client from the live OpenAPI specification.

## Step 1: Verify API Server Is Running

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/docs
```

- **200**: Proceed to Step 2
- **Any other code or connection refused**: Stop and display this message:
  > API server not running at http://localhost:8000. Start it with:
  >
  > - `make run-dev` in `packages/api/`, OR
  > - `docker compose -f infra/docker-compose.dev.yml up aihub-api -d`

## Step 2: Generate the SDK

Run from `packages/web/swiss_ai_hub_web/`:

```bash
cd packages/web/swiss_ai_hub_web && pnpm generate-sdk
```

This uses the config at `packages/web/swiss_ai_hub_web/openapi-ts.config.ts` to fetch the OpenAPI spec from
`http://localhost:8000/api/v1/openapi.json` and regenerate TypeScript files into
`packages/web/swiss_ai_hub_web/sdk/client/` (`types.gen.ts`, `sdk.gen.ts`, `schemas.gen.ts`, `client.gen.ts`,
`transformers.gen.ts`).

## Step 3: Lint Generated Code

```bash
cd packages/web/swiss_ai_hub_web && pnpm lint --fix
```

This auto-fixes formatting issues in the generated TypeScript files.

## Step 4: Verify and Report

1. Confirm generated files exist and are non-empty:

```bash
ls -la packages/web/swiss_ai_hub_web/sdk/client/types.gen.ts packages/web/swiss_ai_hub_web/sdk/client/sdk.gen.ts
```

2. Check for TypeScript compilation errors in the generated output:

```bash
cd packages/web/swiss_ai_hub_web && pnpm nuxi typecheck 2>&1 | head -30
```

3. Report what changed:

```bash
git diff --stat -- packages/web/swiss_ai_hub_web/sdk/client/
```

Summarize: new endpoints added, modified request/response types, removed endpoints, number of files changed.

## Examples

- `/generate-sdk` — Full regeneration workflow (verify, generate, lint, report)

## Troubleshooting

- **API not running**: Start it with `docker compose -f infra/docker-compose.dev.yml up aihub-api -d` or `make run-dev`
  in `packages/api/`
- **pnpm not found**: Run `corepack enable` or install pnpm globally
- **Generation produces no changes**: The API spec may not have changed. Verify your API changes are deployed to the
  running server.
- **Lint errors after generation**: Some generated code may have issues the linter cannot auto-fix. Review the lint
  output and fix manually if needed.

## When to Run

Run this skill after any of these changes:

- Adding new API endpoints (new routes in FastAPI)
- Modifying DTOs or Pydantic response/request models
- Changing route paths or HTTP methods
- Updating query parameters or path parameters
