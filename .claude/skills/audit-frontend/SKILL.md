---
name: audit-frontend
description: Comprehensive frontend code audit. Checks SDK freshness, unused components,
  i18n coverage, composable patterns, accessibility, and Tailwind usage. Reports
  issues with file locations and severity.
allowed-tools: Read, Bash, Grep, Glob
---

# Frontend Code Audit

Run a comprehensive audit of the Nuxt 3 admin interface. Scope via `$ARGUMENTS` (all, i18n, sdk, components, composables, accessibility).

Default scope is `all` if no argument provided.

## Audit 1: SDK Freshness

Check if the generated SDK matches the running API.

1. Check if API is accessible:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/openapi.json
```

2. If accessible, compare the OpenAPI spec endpoints with SDK functions:
   - Read `aihub_web/aihub_web/sdk/client/sdk.gen.ts` for generated functions
   - Fetch `http://localhost:8000/api/v1/openapi.json` and compare paths
   - Report: new endpoints missing from SDK, removed endpoints still in SDK

3. If not accessible, check last modified date of SDK files and warn if older than the latest API code changes.

## Audit 2: Unused Components

Find components that are never referenced:

1. List all `.vue` files in `aihub_web/aihub_web/components/`
2. For each component, derive its auto-import name (e.g., `Agent/Card.vue` → `AgentCard`)
3. Search for usage across all `.vue` and `.ts` files (both `<AgentCard` and `AgentCard` patterns)
4. Report unused components with file paths

## Audit 3: Composable Health

Verify composable patterns are correct:

1. Check all files in `aihub_web/aihub_web/composables/`
2. Verify queries use `defineQuery()` wrapper (not bare `useQuery`)
3. Verify mutations use `defineMutation()` wrapper
4. Check that mutations call `queryCache.invalidateQueries()` after success
5. Verify query keys follow hierarchical pattern `['resource', id?]`
6. Check for hardcoded staleTime values (should use `minutesToMilliseconds()`)
7. Report pattern violations

## Audit 4: i18n Coverage

Cross-check translation keys across all 4 locales:

1. Read all locale files: `aihub_web/aihub_web/i18n/locales/{de,en,fr,it}.yaml`
2. Use English as reference — find keys missing in de/fr/it
3. Find keys in de/fr/it that don't exist in en (orphaned)
4. Check for empty string values
5. Scan `.vue` files for `$t('...')` and `t('...')` calls — find keys used in code but missing from en.yaml
6. Report coverage per language as a percentage

## Audit 5: Accessibility Basics

Check for common accessibility issues:

1. Scan `.vue` files for `<img` tags missing `alt` attributes
2. Check for click handlers on non-interactive elements (divs with `@click` but no `role` or `tabindex`)
3. Verify form inputs have associated labels (FormKit handles this, but custom forms may not)
4. Check for proper heading hierarchy (`h1` → `h2` → `h3`, not skipping levels)
5. Look for hardcoded colors that may not meet contrast requirements

## Audit 6: Tailwind Usage

Verify Tailwind conventions:

1. Check for `<style>` blocks in components (should be minimal — only for PrimeVue overrides)
2. Look for inline `style=""` attributes (should use Tailwind classes)
3. Check for non-standard Tailwind classes (typos, non-existent utilities)

## Report Format

Present findings as a summary table:

| Audit Area | Status | Issues Found | Severity |
|-----------|--------|-------------|----------|
| SDK Freshness | pass/warn/fail | Count | High/Medium/Low |
| Unused Components | pass/warn | Count | Low |
| Composable Health | pass/warn/fail | Count | Medium |
| i18n Coverage | pass/warn/fail | Count + % | Medium |
| Accessibility | pass/warn | Count | Medium |
| Tailwind Usage | pass/warn | Count | Low |

Then list each issue with: file path, line number, description, suggested fix.
