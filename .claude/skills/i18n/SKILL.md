---
name: i18n
description: Comprehensive i18n reference and validation. Covers the dual i18n architecture (frontend Nuxt i18n + backend python-i18n), LocaleHandler/LocaleString class hierarchies, translation file structure and naming, scope inheritance, and when to create vs extend locale files. Also validates key consistency across locales and scans for hardcoded strings. Use when user says 'how does i18n work', 'add translations', 'create locale file', 'check translations', 'find missing i18n keys', 'validate locales', 'i18n coverage', or 'any hardcoded strings'. Do not use for frontend-only i18n config questions — see packages/web/CLAUDE.md instead.
allowed-tools: Read, Bash, Grep, Glob
---

# Internationalization (i18n)

All user-facing strings must be translated into 4 locales: **de** (German), **en** (English), **fr** (French), **it**
(Italian). English (`en`) is the reference/default locale. Fallback chain: requested locale -> `en` -> first available.

## Architecture: Two Separate Systems

Frontend and backend use **completely independent** i18n systems. They share no files, no configuration, and no runtime.

### Frontend (Nuxt `@nuxtjs/i18n`)

- **Config**: `packages/web/swiss_ai_hub_web/nuxt.config.ts` (i18n section, `strategy: 'prefix'`, `lazy: true`)
- **Files**: `packages/web/swiss_ai_hub_web/i18n/locales/{locale}.yaml` — one mega YAML per locale (`.yaml` extension)
- **Usage**: `$t('key.path')` in templates, `t('key.path')` in `<script setup>` via `useI18n()`
- **Navigation**: ALL routes MUST use `localePath()` — URLs include locale prefix (`/en/service/agents`)
- **Key structure**: Nested YAML, accessed via dot-notation: `common.actions.save` ->
  `{ common: { actions: { save: "Save" } } }`

### Backend (python-i18n library)

- **Files**: `{scope}/{name}.{locale}.yml` across multiple packages (`.yml` extension)
- **Usage**: `locale_handler("scope.name.key.path")` at runtime, `ScopeLocaleString.from_i18n_path("scope.name.key")` at
  definition time
- **Key structure**: First two dot segments are `{scope}.{filename}`, the rest navigate YAML nesting

## Backend Translation Files

### File Locations

| Package            | Translation Directory                                              | Scope Prefix |
| ------------------ | ------------------------------------------------------------------ | ------------ |
| `packages/core`    | `packages/core/swiss_ai_hub/core/i18n/translations/lib/`           | `lib`        |
| `packages/core`    | `packages/core/swiss_ai_hub/core/i18n/translations/bot/`           | `bot`        |
| `packages/api`     | `packages/api/swiss_ai_hub/api/i18n/translations/api/`             | `api`        |
| `packages/agent`   | `packages/agent/swiss_ai_hub/agent/i18n/translations/agent/`       | `agent`      |
| `packages/process` | `packages/process/swiss_ai_hub/process/i18n/translations/process/` | `process`    |

**Bot exception**: Bot translations live under `packages/core` (scope `bot/`), NOT in `packages/bot`. Bots use the base
`LocaleHandler`, not a bot-specific subclass.

### Naming Convention

```
{scope}/{descriptive_name}.{locale}.yml
```

Every translation file MUST have exactly 4 variants — one per locale:

```
agent/rag_agent.de.yml
agent/rag_agent.en.yml
agent/rag_agent.fr.yml
agent/rag_agent.it.yml
```

### Path Resolution

The dot-notation path `agent.rag_agent.metadata.name` resolves as:

1. `agent` -> scope directory name
2. `rag_agent` -> YAML filename (without locale/extension)
3. `metadata.name` -> nested keys inside the YAML file

The system searches all registered `load_path` directories for `agent/rag_agent.{locale}.yml`, then navigates
`data["metadata"]["name"]`.

### When to Create a New File vs. Extend an Existing One

**Create a new file** when:

- Adding a **new agent** -> `agent/{agent_name}.{locale}.yml` for metadata/steps/config labels
- Adding a **new process** -> `process/{process_name}.{locale}.yml`
- Adding a **new logical domain** that doesn't fit existing groupings (e.g., a new guard type, a new controller)

**Extend an existing file** when:

- Adding keys to an existing agent/process (e.g., new step in `agent/rag_agent.en.yml`)
- Adding common/shared translations -> `lib/common.{locale}.yml` or `api/common.{locale}.yml`
- Adding event translations -> `lib/events.{locale}.yml`
- Adding guard translations -> `lib/guards.{locale}.yml`

**Naming guidance**: Group by the thing being described, not by where it's used. Agent metadata, step names, config
labels, and error messages for the same agent all go in one file (e.g., `agent/rag_agent.{locale}.yml`). If a file grows
too large (>200 keys), split by sub-domain (e.g., `agent/rag_agent_config.{locale}.yml`).

### Example File Structure

`agent/rag_agent.en.yml`:

```yaml
metadata:
  name: "RAG Agent"
  description: "Retrieves relevant documents and generates answers."
steps:
  retrieve_nodes:
    name: "Retrieve Documents"
    description: "Searches knowledge bases for relevant content."
config:
  context_prompt:
    label: "Context Prompt"
    help: "System prompt used when generating answers."
```

Accessed as: `agent.rag_agent.metadata.name`, `agent.rag_agent.steps.retrieve_nodes.name`, etc.

## LocaleHandler Hierarchy

`LocaleHandler` is the base class for runtime translation lookup. Each sub-package extends it to register its own
translation directory while **inheriting lib-level translations**.

### Base: `LocaleHandler` (`packages/core/swiss_ai_hub/core/i18n/LocaleHandler.py`)

- `DEFAULT_LOCALE = "en"`, `LOCALE_WHITE_LIST = ["de", "en", "fr", "it"]`
- `get_locale_paths()` returns `[packages/core/i18n/translations/]`
- `__call__(key, locale)` -> `i18n.t(key, locale=locale)` — translates a key
- `t_object(key, locale)` -> returns raw YAML data (dict/list) instead of string
- `extract(locale_data, locale)` -> extracts from `dict[str, Any]` or `LocaleString` objects
- `in_locale(locale)` -> returns new handler instance for a different locale

### Sub-package Handlers

Each extends `LocaleHandler` and overrides `get_locale_paths()` to add its own translation directory:

**`ApiLocaleHandler`** (`packages/api/swiss_ai_hub/api/i18n/ApiLocaleHandler.py`):

```python
def get_locale_paths(self) -> list[str]:
    return [*super().get_locale_paths(), self_translations_path]
```

Load paths: `[lib/translations/, api/translations/]` -> can resolve both `lib.*` and `api.*` keys.

**`AgentLocaleHandler`** (`packages/agent/swiss_ai_hub/agent/i18n/AgentLocaleHandler.py`): Same pattern. Load paths:
`[lib/translations/, agent/translations/]`.

**`ProcessLocaleHandler`** (`packages/process/swiss_ai_hub/process/i18n/ProcessLocaleHandler.py`): Same pattern. Load
paths: `[lib/translations/, process/translations/]`.

**Key insight**: All sub-package handlers call `super().get_locale_paths()`, which includes `packages/core`
translations. This means agent code can reference `lib.events.start_event.name` or `lib.guards.context_guard.reason` —
lib-level translations are always available in sub-packages.

### Runtime Usage

In agent/process `@step` methods, the dispatcher injects a locale-aware handler:

```python
async def my_step(self, event: UserMessageEvent, t: AgentLocaleHandler) -> StopEvent:
    error_msg = t("agent.my_agent.errors.not_found")
    lib_msg = t("lib.common.test")  # lib keys work too
    return StopEvent(output=error_msg)
```

## LocaleString Hierarchy

`LocaleString` holds pre-resolved translations for all 4 locales in a single Pydantic model. Used at **definition time**
(class attributes, config labels, event metadata).

### Base: `LocaleString` (`packages/core/swiss_ai_hub/core/i18n/LocaleString.py`)

Fields: `de: str | None`, `en: str | None`, `fr: str | None`, `it: str | None`

Key methods:

- `in_locale(locale)` -> returns string for that locale
- `from_i18n_path(path)` -> creates instance by calling `LocaleHandler(locale)(path)` for each locale
- `as_form(label, ...)` -> creates a `LocaleInput` form element for multi-language editing

### Sub-package LocaleStrings

Each sub-package has its own `LocaleString` subclass that uses the package-specific `LocaleHandler`:

**`AgentLocaleString`** (`packages/agent/swiss_ai_hub/agent/i18n/AgentLocaleString.py`):

```python
@classmethod
def from_i18n_path(cls, path: str) -> Self:
    return cls(
        de=AgentLocaleHandler("de")(path),
        en=AgentLocaleHandler("en")(path),
        fr=AgentLocaleHandler("fr")(path),
        it=AgentLocaleHandler("it")(path),
    )
```

**`ApiLocaleString`** (`packages/api/swiss_ai_hub/api/i18n/ApiLocaleString.py`): Uses `ApiLocaleHandler`.

**`ProcessLocaleString`** (`packages/process/swiss_ai_hub/process/i18n/ProcessLocaleString.py`): Uses
`ProcessLocaleHandler`.

### Definition-Time Usage

Agent/process metadata and config labels use `from_i18n_path()`:

```python
class RetrievalAgent(BaseAgent):
    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.retrieval_agent.metadata.name"
    )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.retrieve.name"),
        description=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.retrieve.description"),
    )
    async def retrieve(self, ...) -> ...:
```

### Direct Construction

For inline values that don't come from YAML files:

```python
LocaleString(de="Hallo", en="Hello", fr="Bonjour", it="Ciao")
```

All 4 locales MUST be provided. This is common in event classes and form elements.

### Persistence: `LocaleStringEntity`

`LocaleStringEntity` (`packages/core/swiss_ai_hub/core/persistence/i18n/LocaleStringEntity.py`) is a MongoEngine
`EmbeddedDocument` with the same 4 fields. Convert between them:

- `LocaleStringEntity.from_locale_string(locale_string)` -> for storage
- `entity.to_locale_string()` -> for runtime

## Validation: Run the Script

Run the deterministic validation script to compare YAML keys across locales:

```bash
uv run python .claude/skills/i18n/scripts/validate-i18n.py $ARGUMENTS
```

`$ARGUMENTS`: `frontend`, `backend`, or `all` (default).

The script flattens nested YAML keys to dot-notation, uses English as reference, and reports missing/extra/empty keys
with coverage percentages. **Present the script output to the user as-is.**

## Validation: LocaleString Completeness

The script does not cover inline `LocaleString(...)` instances. Check manually:

```bash
grep -rn 'LocaleString(' packages/agent/ packages/process/ --include='*.py'
```

Each `LocaleString(...)` must have all 4 keyword arguments: `de=`, `en=`, `fr=`, `it=`.

## Validation: Hardcoded Strings in New Code

Review `git diff main -- '*.py' '*.vue' '*.ts'` for hardcoded user-facing strings.

**Frontend**: Flag literal text in HTML elements, hardcoded `label=`/`placeholder=`/`title=` props, toast messages
without `$t()` or `t()`.

**Backend**: Flag `LocaleString()` with fewer than 4 locales, hardcoded strings in
`display_chunk()`/`display_thought()`, literal form element `label=`/`help=` without `LocaleString`.

**Do NOT flag**: Log messages, internal exceptions, test files, comments, NATS subjects, config keys, docstrings.

## Validation: Frontend Template Key Usage

Extract i18n keys from Vue templates and verify they exist in `en.yaml`:

```bash
grep -rhoP "\$t\(['\"]([^'\"]+)['\"]\)" packages/web/swiss_ai_hub_web/ --include='*.vue' | sort -u
```

Ignore dynamic keys like `$t(variable)`.
