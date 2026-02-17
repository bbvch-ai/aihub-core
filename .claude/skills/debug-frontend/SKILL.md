---
name: debug-frontend
description: >-
  Debug the Nuxt 3 admin UI using Playwright MCP for visual inspection, console error analysis,
  and network request tracing. Use when user says 'UI is broken', 'page not loading', 'frontend
  bug', 'console errors', 'API call failing in UI', 'component not rendering', 'blank page',
  'verify my UI changes', or 'check the admin interface'. Captures screenshots, DOM snapshots,
  and network traces.
allowed-tools: Read, Bash, Grep, Glob
---

# Frontend Debugging Assistant

Debug the Nuxt 3 admin interface visually. Issue description or page URL via `$ARGUMENTS`.

## Prerequisites

The admin UI must be running at http://localhost:3000. If not running:

```bash
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm dev
```

## Step 1: Navigate to the Page

Use the Playwright MCP `browser_navigate` tool to open the page. Common entry points:

- **Dashboard**: `http://localhost:3000/en`
- **Agents**: `http://localhost:3000/en/service/agents`
- **Processes**: `http://localhost:3000/en/service/processes`
- **Threads**: `http://localhost:3000/en/service/threads`
- **Knowledge**: `http://localhost:3000/en/service/databases`
- **Users**: `http://localhost:3000/en/service/users`
- **Roles**: `http://localhost:3000/en/service/roles`

## Step 2: Capture Page State

Use these Playwright MCP tools to gather diagnostic information:

1. **`browser_snapshot`**: Get the accessibility tree (DOM structure, interactive elements)
2. **`browser_take_screenshot`**: Visual capture of the current state
3. **`browser_console_messages`** with `level: "error"`: Check for JavaScript errors
4. **`browser_network_requests`**: Inspect API calls (failed requests, wrong payloads)

## Step 3: Diagnose Common Issues

### API Errors (4xx/5xx)

1. Check `browser_network_requests` for failed API calls
2. Look at the request URL and response status
3. Cross-reference with SDK functions in `aihub_web/aihub_web/sdk/client/`
4. Check if the API server is running (`curl http://localhost:8000/api/v1/docs`)

### Rendering Issues

1. Take a screenshot to see the visual state
2. Use `browser_snapshot` to check the DOM structure
3. Look for missing data (composable not returning data)
4. Check if `StructuralColumn` has `loading: true` (blocks child rendering)

### Auth/Redirect Issues

1. Check if redirected to `/auth/login`
2. Verify the OIDC plugin is configured: `aihub_web/aihub_web/plugins/oidc-client.ts`
3. Check `middleware/auth.global.ts` for route guard logic
4. In dev mode, fake auth should bypass OIDC

### i18n Missing Keys

1. Look for raw key paths displayed instead of translated text (e.g., `agent.title` shown literally)
2. Check locale files: `aihub_web/aihub_web/i18n/locales/en.yaml`
3. Verify the key exists at the expected path

### Component Not Updating

1. Check Pinia-Colada query keys — mismatched keys prevent cache hits
2. Verify `enabled` flag on queries (must be `true` or a reactive ref)
3. Check if mutation calls `queryCache.invalidateQueries()` after success
4. Use `browser_evaluate` to inspect Vue component state if needed

## Step 4: Interact and Reproduce

Use Playwright MCP to interact with the UI:

- **`browser_click`**: Click buttons, links, menu items
- **`browser_type`**: Fill form fields
- **`browser_fill_form`**: Fill multiple form fields at once
- **`browser_select_option`**: Select dropdown values
- **`browser_press_key`**: Keyboard shortcuts (Escape, Enter, Tab)

Reproduce the issue step by step and capture screenshots at each stage.

## Step 5: Trace to Source Code

Once the issue is identified:

1. Find the page component: `aihub_web/aihub_web/pages/service/<resource>/`
2. Find composables: `aihub_web/aihub_web/composables/<resource>/`
3. Find child components: `aihub_web/aihub_web/components/<Resource>/`
4. Check SDK types: `aihub_web/aihub_web/sdk/client/`

## Step 6: Report

Provide a structured report with:

- **What was observed**: Screenshot + console errors + failed network requests
- **Root cause**: Which file and line is responsible
- **Suggested fix**: Specific code change to resolve the issue

## Examples

- `/debug-frontend the agents page shows a blank table` -- Navigate to agents page, check network requests for API
  failures, inspect DOM for missing data bindings
- `/debug-frontend console errors on the dashboard` -- Open dashboard, capture console errors, trace to source component
- `/debug-frontend verify my changes to the roles page` -- Navigate to roles page, take screenshot, check for
  regressions

## Troubleshooting Quick Reference

| Symptom                   | Likely Cause                                      | Where to Look                                                  |
| ------------------------- | ------------------------------------------------- | -------------------------------------------------------------- |
| Blank page                | JavaScript error blocking render                  | `browser_console_messages` with level "error"                  |
| Spinner never stops       | API call hanging or query `enabled` flag is false | `browser_network_requests` + composable `enabled` prop         |
| 401 on API calls          | Auth not configured for dev                       | `plugins/oidc-client.ts`, check dev mode fake auth             |
| Missing translations      | i18n key not in locale file                       | `i18n/locales/en.yaml`, search for the raw key                 |
| Stale data after mutation | Missing `queryCache.invalidateQueries()`          | Composable mutation `onSuccess` callback                       |
| Component not found       | Auto-import name mismatch                         | Verify component file path matches Nuxt auto-import convention |
