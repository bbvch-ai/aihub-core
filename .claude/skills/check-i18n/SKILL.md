---
name: check-i18n
description: Validate that all locale files have matching keys across languages (de, en, fr, it). Finds missing translations, orphaned keys, and incomplete LocaleStrings. Use when user says 'check translations', 'find missing i18n keys', 'validate locales', 'are all strings translated', or 'i18n coverage'. Covers frontend YAML, backend, and agent locales.
allowed-tools: Read, Bash, Grep, Glob
---

# Internationalization Validation

Validate i18n key consistency across all languages. Scope via `$ARGUMENTS`: `frontend`, `backend`, `agents`, or `all`
(default).

## Step 1: Validate Frontend Locale Files

Read all 4 YAML locale files:

- `aihub_web/aihub_web/i18n/locales/de.yaml`
- `aihub_web/aihub_web/i18n/locales/en.yaml`
- `aihub_web/aihub_web/i18n/locales/fr.yaml`
- `aihub_web/aihub_web/i18n/locales/it.yaml`

Use English (`en.yaml`) as the reference. For each other language, identify:

- **Missing keys**: Present in `en` but absent in the target language
- **Extra keys**: Present in the target language but absent in `en`
- **Empty values**: Keys with empty string values (translation placeholder left blank)

**Expected output** — a table per language:

| Language | Total Keys | Missing | Extra | Empty | Coverage |
| -------- | ---------- | ------- | ----- | ----- | -------- |
| de       | 210        | 3       | 0     | 1     | 98.1%    |
| fr       | 205        | 8       | 0     | 2     | 95.2%    |
| it       | 200        | 13      | 0     | 0     | 93.8%    |

## Step 2: Validate Backend Locale Files

Check locale files in these directories:

- `aihub_lib/aihub_lib/i18n/`
- `aihub_api/aihub_api/i18n/`

Apply the same missing/extra/empty key checks as Step 1.

## Step 3: Validate Agent LocaleString Completeness

1. Search for `LocaleString(` patterns across the codebase (primarily in `aihub_agent/` and `aihub_process/`)
2. Verify each `LocaleString` instance has all 4 locales: `de`, `en`, `fr`, `it`
3. Flag any `LocaleString` with fewer than 4 entries, listing file and line number

## Step 4: Check Template Key Usage

1. Search Vue files (`aihub_web/aihub_web/**/*.vue`) for `$t('...')` and `t('...')` patterns
2. Extract every referenced i18n key
3. Verify each key exists in at least the English locale file (`en.yaml`)
4. Report any keys used in templates but missing from locale files

## Step 5: Summary Report

Produce a final summary with:

- Total keys per area (frontend, backend, agents)
- Coverage percentage per language
- List of incomplete `LocaleString` instances with file paths
- List of template keys missing from locale files
- Prioritized action items (most impactful gaps first)

## Examples

- `/check-i18n` — Validate all i18n (frontend + backend + agents)
- `/check-i18n frontend` — Validate only frontend YAML locale files
- `/check-i18n agents` — Check only agent `LocaleString` completeness

## Troubleshooting

- **YAML parse errors**: A locale file may have invalid YAML syntax. Run
  `python -c "import yaml; yaml.safe_load(open('path'))"` to verify.
- **Nested key mismatches**: Keys are compared as flattened dot-notation paths (e.g., `settings.theme.dark`). Ensure
  nesting structure matches across files.
- **False positives in template scan**: Dynamic keys like `$t(variableName)` cannot be statically checked. These are
  reported but can be ignored.
