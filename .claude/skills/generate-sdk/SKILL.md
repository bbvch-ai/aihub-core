---
name: generate-sdk
description: Regenerate the frontend TypeScript API client from the OpenAPI spec.
  Verifies API server is running, runs the code generator, and lints the output.
  Use when user says 'regenerate SDK', 'update API client', 'sync frontend types',
  'generate TypeScript client', or 'API changed, update frontend'.
  Requires the API server to be running on localhost:8000.
disable-model-invocation: true
allowed-tools: Bash, Read
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
  > - `make run-dev` in `aihub_api/`, OR
  > - `docker compose -f docker-compose.dev.yml up aihub-api -d`

## Step 2: Generate the SDK

```bash
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm generate-sdk
```

**Expected output**: TypeScript files regenerated in the SDK output directory. Watch for errors in the generation log.

## Step 3: Lint Generated Code

```bash
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm lint --fix
```

This auto-fixes formatting issues in the generated TypeScript files.

## Step 4: Report Changes

```bash
cd /home/user/aihub-core && git diff --stat
```

Summarize what changed:
- New endpoints added
- Modified request/response types
- Removed endpoints
- Number of files changed

## Examples

- `/generate-sdk` — Full regeneration workflow (verify, generate, lint, report)

## Troubleshooting

- **API not running**: Start it with `docker compose -f docker-compose.dev.yml up aihub-api -d` or `make run-dev` in `aihub_api/`
- **pnpm not found**: Run `corepack enable` or install pnpm globally
- **Generation produces no changes**: The API spec may not have changed. Verify your API changes are deployed to the running server.
- **Lint errors after generation**: Some generated code may have issues the linter cannot auto-fix. Review the lint output and fix manually if needed.

## When to Run

Run this skill after any of these changes:
- Adding new API endpoints (new routes in FastAPI)
- Modifying DTOs or Pydantic response/request models
- Changing route paths or HTTP methods
- Updating query parameters or path parameters
