---
name: check-i18n
description: Validate i18n key consistency across all locale files (de, en, fr, it). Runs a deterministic Python script that compares YAML keys across frontend and backend translation files, checks LocaleString completeness, template key usage, and scans the git diff for hardcoded user-facing strings that should be extracted into i18n. Use when user says 'check translations', 'find missing i18n keys', 'validate locales', 'are all strings translated', 'i18n coverage', or 'any hardcoded strings'. Do not use for adding new translations or modifying locale files — this is read-only validation.
allowed-tools: Read, Bash, Grep, Glob
---

# Internationalization Validation

Validate i18n key consistency across all 4 languages (de, en, fr, it). English (`en`) is the reference locale.

## i18n Architecture Overview

The project has two completely separate i18n systems:

**Frontend** (Nuxt `@nuxtjs/i18n`): Single YAML file per locale, nested keys, lazy-loaded.

- `aihub_web/aihub_web/i18n/locales/{locale}.yaml` (note: `.yaml` not `.yml`)

**Backend** (python-i18n): Multiple YAML files per scope, flat or shallow keys, loaded by `LocaleHandler`.

- `aihub_lib/aihub_lib/i18n/translations/{scope}/{name}.{locale}.yml`
- `aihub_api/aihub_api/i18n/translations/api/{name}.{locale}.yml`
- `aihub_agent/aihub_agent/i18n/translations/agent/{name}.{locale}.yml`
- `aihub_process/aihub_process/i18n/translations/process/{name}.{locale}.yml`

Bot translations live in `aihub_lib` under `bot/` scope — `aihub_bot` has no own translation files.

**LocaleString**: Pydantic model for inline multi-language values (not YAML files). Used in agent/process configs and
events. Each instance must have all 4 locales.

**Default locale**: English (`en`). Fallback chain: requested locale → `en` → first available.

## Step 1: Run the Validation Script

Run the deterministic validation script. It parses all YAML files, flattens nested keys to dot-notation, and compares
key sets across locales using English as reference.

```bash
uv run python .claude/skills/check-i18n/scripts/validate-i18n.py $ARGUMENTS
```

`$ARGUMENTS` accepts: `frontend`, `backend`, or `all` (default).

The script covers:

- **Frontend**: 4 files in `aihub_web/aihub_web/i18n/locales/`
- **Backend**: All `{name}.{locale}.yml` files across `aihub_lib`, `aihub_api`, `aihub_agent`, `aihub_process`

For each locale it reports: total keys, missing keys, extra keys, empty values, coverage percentage. Non-reference
locales with issues get detailed key lists.

**Present the script output to the user as-is** — it is the primary deliverable.

## Step 2: Validate LocaleString Completeness (if `$ARGUMENTS` is `agents` or `all`)

The script does not cover inline `LocaleString(...)` instances. Check these manually:

1. Search for `LocaleString(` across `aihub_agent/` and `aihub_process/`:

```bash
grep -rn 'LocaleString(' aihub_agent/ aihub_process/ --include='*.py'
```

2. Each `LocaleString(...)` must have all 4 keyword arguments: `de=`, `en=`, `fr=`, `it=`
3. Flag any instance with fewer than 4 locales, listing file and line number
4. Common location: agent config files (`agents/*/config/`), process configs, event classes

## Step 3: Check Frontend Template Key Usage (if `$ARGUMENTS` is `frontend` or `all`)

1. Extract all i18n keys from Vue templates:

```bash
grep -rhoP "\\\$t\(['\"]([^'\"]+)['\"]\)" aihub_web/aihub_web/ --include='*.vue' | sort -u
grep -rhoP "(?<![\\$])t\(['\"]([^'\"]+)['\"]\)" aihub_web/aihub_web/ --include='*.vue' | sort -u
```

2. Read `aihub_web/aihub_web/i18n/locales/en.yaml` and flatten all keys
3. Report any template key not found in the English locale file
4. Ignore dynamic keys like `$t(variable)` — these cannot be statically validated

## Step 4: Check for Hardcoded Strings in New Code

Review the current git diff for hardcoded user-facing strings that should be extracted into i18n locale files.

1. Get the diff against main:

```bash
git diff main -- '*.py' '*.vue' '*.ts'
```

2. In **added lines** (`+` prefix), look for hardcoded user-facing strings — these are signs of missing i18n:

   **Frontend (`.vue`, `.ts`)**: Any literal text in templates that a user would see. Correct pattern is `$t('key')` or
   `t('key')`. Flag:

   - Text content in HTML elements: `<p>Some text</p>` instead of `<p>{{ $t('key') }}</p>`
   - Hardcoded `label=`, `placeholder=`, `header=`, `title=`, `message=` prop values with literal strings
   - Toast/confirm messages with literal strings instead of `t('key')`
   - `aria-label` with literal strings (should also be translated)

   **Backend (`.py`)**: User-facing messages that get sent to the frontend or displayed to users. Flag:

   - Literal strings in `LocaleString()` constructors that only have 1-2 locales instead of all 4
   - Hardcoded strings passed to `display_chunk()`, `display_thought()`, or similar displayer methods
   - Exception messages shown to users (not internal debug/log messages — those are fine in English)
   - Literal strings in form element `label=`, `help=`, `placeholder=` that should use `LocaleString`

3. **Do NOT flag** (these are acceptable in English only):

   - Log messages (`logger.info/debug/warning/error`)
   - Internal exception messages not shown to users
   - Test files
   - Code comments
   - NATS subject strings, config keys, environment variable names
   - Python docstrings

4. For each hardcoded string found, report the file, line number, the string, and suggest whether it should use
   `$t('key')` (frontend), `LocaleString(de=..., en=..., fr=..., it=...)` (backend config/events), or
   `self.locale_handler('key')` (backend runtime).

## Step 5: Summary

Combine script output with manual checks into a final summary:

- Total keys per area (frontend, each backend scope)
- Coverage percentage per language per area
- Incomplete `LocaleString` instances with file paths
- Template keys missing from locale files
- Prioritized action items (most impactful gaps first)

## Examples

- `/check-i18n` — Full validation (script + LocaleString + template keys)
- `/check-i18n frontend` — Frontend YAML files + template key usage
- `/check-i18n backend` — Backend YAML files only (all 4 scopes)

## Troubleshooting

- **YAML parse errors**: `uv run python -c "import yaml; yaml.safe_load(open('path'))"`
- **Nested key mismatches**: Keys are flattened to dot-notation (e.g., `settings.theme.dark`). Mismatched nesting
  structure shows as both missing and extra keys in the same group.
- **False positives in template scan**: Dynamic keys like `$t(variableName)` cannot be statically checked.
- **Script path**: `.claude/skills/check-i18n/scripts/validate-i18n.py`
