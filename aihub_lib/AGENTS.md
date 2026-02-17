# aihub_lib - Foundational Library

**Purpose**: Shared infrastructure library used by ALL AI-Hub services. Code belongs here if used by 2+ services.

Tech Stack & Paradigms: NATS pub-sub (nats-py) with typed Pydantic events. Hierarchical event model: Control (workflow) vs Display (observability). MongoEngine ODM for MongoDB (FerretDB). LlamaIndex Core + extensions (vector stores: Milvus/Azure AI Search, storage: MongoDB docstore, readers: file, postprocessors: Cohere rerank, embeddings/LLMs: OpenAI-like). Redis v5 client for Valkey state storage. Azure SDK suite (speech, cosmos, search, storage, document intelligence, cognitive services). OpenTelemetry full instrumentation suite (SDK, API, exporters, semantic conventions) + OpenInference for LLM tracing. Langfuse for observability and evaluation. FastAPI for REST. python-i18n for translations. Pydantic v2 + pydantic-settings. OpenAI SDK, google-genai, transformers (HuggingFace). MinerU + MarkItDown for document processing. boto3 for AWS. cachetools for TTL caching. colorlog for logging. fsspec for filesystem abstraction. pytest + pytest-bdd + pytest-mock for testing.

## Scope Responsibility

Foundation for event-driven architecture, authentication/authorization, internationalization, and testing utilities. NOT for service-specific business logic.

## Folder Structure

```
aihub_lib/
├── auth/                      # Authentication & authorization
│   ├── access/                # Permission-based access control (AccessChecker)
│   ├── dependencies/          # Auth handlers (OAuth2, Token, DevOnly)
│   └── identity/              # Identity providers (Azure AD, Graph, DevOnly)
├── nats/                      # Event-driven messaging (core pattern)
│   ├── events/                # Event type hierarchy (CRITICAL to understand)
│   ├── dispatcher/            # Workflow orchestration (BaseDispatcher)
│   ├── publishers/            # Event publishing
│   └── subscribers/           # Event subscription
├── generative_ai/             # AI/ML utilities
├── i18n/                      # Internationalization (4 languages: de, en, fr, it)
├── persistence/               # Database abstractions (MongoEngine)
├── routes/                    # FastAPI base controllers
└── testing/                   # Testing utilities (BDD, auth, async)
```

## Key Concepts

**Event Hierarchy** (CRITICAL):

Used by agents:

- **ControlEvent**: Drives workflow execution. Only type that can control flow.
- **DisplayEvent**: UI/monitoring only. Never affects control flow.

Used by agentic-processses:

- **WorkEvent**: Signals work completion (AgentWorkEvent, HumanWorkEvent, etc.).
- **WorkRequestEvent**: Delegates work to entities.

**Auth Pattern**:

- **AuthHandler**: Extracts/validates credentials from requests → UserIdentity.
- **IdentityProvider**: Retrieves user details from identity systems.
- Examples: `/home/user/aihub-core/aihub_lib/aihub_lib/auth/dependencies/`, `/home/user/aihub-core/aihub_lib/aihub_lib/auth/identity/`

**Permission System**:

- Hierarchical: `aihub.[user|admin].<resource>.<subresource>.<id>`
- Wildcards: `*` (single level), `>` (multi-level), `?*`, `?>`
- Check: `AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id)`

**Persistence Pattern**:

- Entities = MongoEngine `Document` + repository methods as `@classmethod`
- Example: `ResourceEntity.by_name(name)` combines schema + data access

**i18n**:

- Default locale: German (`de`). Required: `de`, `en`, `fr`, `it`.
- `LocaleString` for multi-language, `LocaleHandler` for runtime resolution.
- Translations: `/home/user/aihub-core/aihub_lib/aihub_lib/i18n/translations/`

## Adding Code

**When to add here**:

- Used by 2+ services
- Core infrastructure (auth, events, config, testing)
- Shared abstractions (base classes, interfaces)

**When NOT to add**:

- Service-specific logic
- Single-use implementations

## Testing

**BDD**: Use `pytest-bdd` for complex flows. Async support via `@async_test` decorator.
**Location**: `/home/user/aihub-core/aihub_lib/tests/`

## Pre-Commit

```bash
make pr-ready  # Format + lint + type check
make test      # Run tests (exclude Azure: -k "not azure")
```

## Essential Files

- Event hierarchy: `/home/user/aihub-core/aihub_lib/aihub_lib/nats/events/`
- Base dispatcher: `/home/user/aihub-core/aihub_lib/aihub_lib/nats/dispatcher/BaseDispatcher.py`
- Auth handlers: `/home/user/aihub-core/aihub_lib/aihub_lib/auth/dependencies/`
- Access control: `/home/user/aihub-core/aihub_lib/aihub_lib/auth/access/AccessChecker.py`
- Testing utils: `/home/user/aihub-core/aihub_lib/aihub_lib/testing/`

## Quick Reference

**Create new event**:

1. Inherit from appropriate base (`ControlEvent`, `DisplayEvent`, etc.)
2. Place in `/home/user/aihub-core/aihub_lib/aihub_lib/nats/events/<category>/`
3. Auto-registers on import

**Create auth handler**:

1. Inherit from `AuthHandler`
2. Implement `__call__(self, request: Request) -> UserIdentity`
3. Example: `/home/user/aihub-core/aihub_lib/aihub_lib/auth/dependencies/OAuth2AuthHandler/`

**Create identity provider**:

1. Inherit from `IdentityProvider`
2. Implement `get_user_identity_by_oid()`, `get_user_identity_by_email()`
3. Example: `/home/user/aihub-core/aihub_lib/aihub_lib/auth/identity/MicrosoftGraphIdentityProvider/`
