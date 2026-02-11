---
name: generate-sdk
description: Regenerate the frontend API SDK from the OpenAPI specification.
  Ensures the API server is accessible, runs the code generator, and verifies
  the output. Use after modifying API endpoints or DTOs.
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Frontend API SDK Generation

Regenerate the TypeScript API client from the OpenAPI spec.

## Step 1: Verify API Accessibility

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/docs
```

If NOT running, warn: "API server not running at http://localhost:8000. Start with `make run-dev` in aihub_api/ or `docker compose -f docker-compose.dev.yml up aihub-api`"

## Step 2: Generate SDK

```bash
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm generate-sdk
```

## Step 3: Lint Generated Code

```bash
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm lint --fix
```

## Step 4: Report Changes

Run `git diff --stat` to show what files changed. Summarize: new endpoints, modified types, removed endpoints.

## When to Run

After: adding new API endpoints, modifying DTOs, changing route paths, updating Pydantic response models.
