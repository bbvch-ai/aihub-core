---
name: check-i18n
description: Validate that all locale files have matching keys across languages.
  Identifies missing translations and orphaned keys. Checks frontend and backend
  i18n. Use after adding UI text or modifying translations.
allowed-tools: Read, Bash, Grep, Glob
---

# Internationalization Validation

Validate i18n key consistency. Scope via `$ARGUMENTS` (frontend, backend, agents, or all).

## Frontend i18n

### Step 1: Load and compare locale files

Read all 4 YAML locale files:
- `aihub_web/aihub_web/i18n/locales/de.yaml`
- `aihub_web/aihub_web/i18n/locales/en.yaml`
- `aihub_web/aihub_web/i18n/locales/fr.yaml`
- `aihub_web/aihub_web/i18n/locales/it.yaml`

Use English (`en.yaml`) as the reference. Compare key sets:
- **Missing keys**: Keys in `en` but not in other languages
- **Extra keys**: Keys in other languages but not in `en`
- **Empty values**: Keys with empty string values

### Step 2: Report

Table with: language, total keys, missing, extra, empty, coverage percentage.

## Backend i18n

Check locale files in:
- `aihub_lib/aihub_lib/i18n/`
- `aihub_api/aihub_api/i18n/`

## Agent LocaleString Completeness

Search for `LocaleString(` patterns. Verify each has all 4 locales: de, en, fr, it. Flag any with fewer than 4 entries.

## Template Usage

Search Vue files for `$t('...')` and `t('...')` patterns. Verify each referenced key exists in at least the English locale file.

## Summary

Report total keys, coverage per language, incomplete LocaleStrings, and action items.
