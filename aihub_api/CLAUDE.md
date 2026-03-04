# aihub_api - REST API, WebSocket Gateway & MCP Server

**Purpose**: FastAPI REST API + WebSocket gateway + MCP server. Bridges frontends and external clients to AI-Hub
services via the Swiss AI Agent Protocol.

## Scope Responsibility

HTTP endpoints, real-time WebSocket events, agent/process discovery, thread management, authentication enforcement,
protocol conversion (NATS events ↔ REST/WebSocket/SSE/OpenAI). NOT business logic — delegate to services.

## Folder Structure

```
aihub_api/
├── app/main.py                 # Production entry — registers all controllers
├── aihub_api/
│   ├── routes/                 # Controllers + Services + DTOs (by domain)
│   │   ├── agent/              # Agent class/instance management
│   │   ├── thread/             # Conversation management
│   │   ├── user/               # User management
│   │   ├── my_account/         # Current user profile & dashboard
│   │   ├── auth_provider/      # Auth provider discovery (Keycloak IdPs)
│   │   ├── openai/             # OpenAI-compatible chat/embeddings/audio/images
│   │   ├── event/              # Event streaming + WebSocket endpoint
│   │   ├── process/            # Process orchestration
│   │   ├── knowledge/          # Vector DB / RAG operations
│   │   ├── memory/             # User & organization memory
│   │   ├── evaluation/         # Dataset & evaluation management
│   │   ├── role/               # Permission & role management
│   │   ├── file/               # File upload/download
│   │   ├── model/              # LLM model access
│   │   ├── notification/       # User notifications
│   │   ├── token/              # API token management
│   │   ├── translation/        # Translation service
│   │   ├── suite/              # Suite management
│   │   ├── health/             # Health & readiness checks
│   │   ├── i18n/               # Locale endpoints
│   │   ├── auth_provider/      # Identity provider discovery (unauthenticated, Keycloak Admin API, Redis cache)
│   │   └── parsing/            # Document parsing (MinerU)
│   ├── services/               # Dynamic endpoint discovery (NATS-based)
│   ├── events/                 # EventModelCreationService (Jambo)
│   ├── rpc/                    # NATS RPC responders (agent/process config)
│   ├── sockets/                # WebSocket manager, sender, event wrapping
│   ├── runners/                # ApiRunner, ApiTestRunner, simulation runners
│   ├── i18n/                   # Locale handling, translations, middleware
│   ├── pagination/             # PageNumber, PageSize types
│   ├── persistance/            # Event persistence to MongoDB
│   ├── audio/                  # Audio chunking service
│   └── testing/                # Auth bypass utilities for tests
├── playground/testing/          # Interactive test server + test suite
│   ├── main.py                 # Dev server entry point
│   └── tests/                  # All API tests (by domain)
├── Makefile                    # run-dev, run-prod, test, pr-ready
└── Dockerfile                  # Production container build
```

## API as an SDK

`aihub_api` serves dual purposes: it IS the production API, and it's an importable Python package. End-users can import
controllers from `aihub_api.routes.*`, mount them on an `ApiRunner`, and build custom APIs with any subset of endpoints.

**Production API**: `app/main.py` registers all controllers and creates the app. New controllers MUST be registered
here, otherwise they won't be served. `runner.create_app()` also mounts an MCP server at `/mcp`, making the API
available as a Claude Code MCP tool for testing.

**Commands**: `make run-dev` (uvicorn with hot reload on :8000), `make run-prod` (gunicorn multi-worker).

**Docker**: `Dockerfile` builds the production image using `make run-prod` as entrypoint. End-users can also build their
own Docker image importing only the controllers they need.

## Controller-Service-DTO Pattern

**Controller** → HTTP endpoint definition, auth, routing. Fluent builder returning `Self`. **Service** → Business logic
with `@staticmethod` + `@trace_fn`. Stateless. Calls entities for persistence. **DTO** → Pydantic v2 models.
`@classmethod` factories (`from_entity()`, `from_discovery_event()`). `in_locale(t)` for localization. **Entity** →
MongoEngine documents with repository classmethods (lives in `aihub_lib/persistence/`).

Controllers must define class attributes: `name` and `description` via `ApiLocaleString.from_i18n_path()`, plus `icon`
(Iconify identifier). See `routes/agent/AgentController.py` for the reference implementation.

Registration in `app/main.py`:

```python
runner.mount(MyController(auth=auth).create_resource().get_resource().delete_resource())
```

## FastAPI Dependencies

Custom dependencies injected via `Depends()` and `Security()` — use these in every endpoint:

| Dependency                                        | Provides                          | Source                             |
| ------------------------------------------------- | --------------------------------- | ---------------------------------- |
| `Security(self.user_with_permission(template))`   | `UserIdentity` + permission check | `Controller` base class            |
| `Depends(use_locale)` / `use_locale_ws`           | `ApiLocaleHandler` (i18n)         | `aihub_api/i18n/dependencies/`     |
| `Depends(use_nats)` / `use_nats_ws`               | NATS client                       | `aihub_lib/nats/dependencies/`     |
| `Depends(use_external_agent_event_distributor)`   | Publish events to agents          | `aihub_lib/nats/distributor/`      |
| `Depends(use_external_process_event_distributor)` | Publish events to processes       | `aihub_lib/nats/distributor/`      |
| `Depends(use_s3)` / `use_s3_public`               | S3 client (internal / presigned)  | `aihub_lib/infrastructure/s3/`     |
| `Depends(use_milvus)`                             | Milvus vector DB client           | `aihub_lib/infrastructure/milvus/` |
| `Depends(use_redis)`                              | Redis/Valkey client               | `aihub_lib/infrastructure/redis/`  |
| `Depends(use_vector_store_factory)`               | Vector store creation             | `aihub_lib/infrastructure/milvus/` |
| `Depends(use_ws_manager)` / `use_ws_manager_ws`   | WebSocket connection manager      | `aihub_api/sockets/`               |

All infrastructure clients are initialized in `runners/lifetime/lifetime_manager.py` and stored in `app.state`.

## i18n System

**Hierarchy**: `LocaleString`/`LocaleHandler` (aihub_lib) → `ApiLocaleString`/`ApiLocaleHandler` (aihub_api extends with
API-specific translation paths).

**Translation files**: `i18n/translations/api/controllers.{locale}.yml` and `common.{locale}.yml` (4 locales: de, en,
fr, it). Path format: `api.controllers.agent.name` resolves to `controllers.{locale}.yml` → key `agent.name`.

**Controller usage**: Always use `ApiLocaleString.from_i18n_path()` for `name` and `description` class attributes. Add
translation keys for new controllers in all 4 locale files.

**Endpoint flow**: `I18nMiddleware` extracts locale from request headers (`lang`, `locale`, `Accept-Language`), query
params, or path params (default: `"de"`, whitelist: `["de", "en", "fr", "it"]`). Injected via `Depends(use_locale)` as
`t: LocaleHandler`. Pass to services and DTOs. DTOs with user-facing strings implement `in_locale(t)`.

## Authentication & Authorization

**Permission template**: `aihub.[user|admin].<resource>.{path_param}` — path parameters (`{agent_class}`, `{agent_id}`,
`{thread_id}`) are interpolated from the URL at request time.

**Wildcards**: `?>` matches single level, `>` matches multiple levels.

**Controller integration**: `Security(self.user_with_permission("aihub.user.agent.{agent_class}.?>"))` handles auth +
permission validation + OpenTelemetry span enrichment (user ID, email, roles, resource context) automatically.

**Service-level checks**: `AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id)` for fine-grained
authorization beyond endpoint-level permissions.

## Dynamic Endpoint Registration

The API doesn't hardcode agent or process endpoints. Discovery services dynamically register/deregister FastAPI routes
based on what's available on NATS.

**`AgentEndpointsDiscoveryService`**: Every 60 seconds, broadcasts `ClassDiscoveryRequestEvent` via NATS. Online agents
respond with metadata (start/stop/HITL event specs, config schema, form definition). The service creates FastAPI
endpoints for each agent class's events — both regular and streaming variants. When agents go offline, their endpoints
are removed and the OpenAPI schema is invalidated.

**`ProcessEndpointsDiscoveryService`**: Same pattern for processes. Registers form GET/POST endpoints for human input
steps and data POST endpoints for programmatic input.

**`ModelCreationService`** + **`EventModelCreationService`**: Convert agent event JSON schemas into Pydantic models at
runtime using `jambo.SchemaConverter.build()`. Input models exclude framework fields (`event_id`, `created_at`, `user`,
`locale`). Output models exclude internal fields (`_event_name`, `_parent_event_names`). These models power the dynamic
endpoint request/response validation and OpenAPI documentation.

## Agent-API Communication

**API → Agents** (pub/sub): `ExternalAgentEventDistributor` publishes `StartEvent`/`HumanInTheLoopResponseEvent` to
agent NATS topics. Agents subscribe to thread-specific subjects.

**Agents → API** (pub/sub): Agents publish `DisplayEvent`s. The API has two parallel NATS subscribers: `EventPersister`
stores ALL events to MongoDB (audit trail). `WebSocketSender` broadcasts display events to connected WebSocket clients
in real-time, wrapped in `ContextualizedAgentEvent` (adds agent_class, thread_id, locale context).

**Agents → API** (RPC): `AgentConfigResponder` and `ProcessConfigResponder` serve configuration data via NATS
request-reply on `aihub.rpc.config.agent.*.*` / `aihub.rpc.config.process.*.*`. Agents fetch their config at runtime
without needing it baked into event payloads.

**Protocol conversion**: WebSocket sends `ContextualizedAgentEvent` JSON. OpenAI-compatible SSE streams
`ChatCompletionChunk`. Aggregated endpoint collects events into `ChatCompletion` response.

## WebSocket

- Endpoint: `/api/v1/events/ws` (in `EventController`)
- Auth: First message must contain `{"token": "Bearer ..."}` — validated against auth handler
- Read-only from client: inbound messages after auth are ignored (security)
- Multi-connection per user: `WebSocketManager` tracks connections per user ID, syncs across tabs/devices
- Event routing: `WebSocketSender` finds thread participants via `ThreadEntity`, broadcasts to all their connections

## Lifetime Manager

`runners/lifetime/lifetime_manager.py` — FastAPI lifespan context manager wiring all infrastructure at startup.

**Startup order**: MongoDB → Redis/Milvus/S3 → NATS + JetStream → event persistence subscribers → WebSocket
infrastructure → event distributors → RPC responders → discovery services → DB initialization (default roles, knowledge
buckets, Langfuse provisioning).

All resources stored in `app.state`, accessible via the dependencies listed above.

## Testing

**Location**: `playground/testing/tests/<domain>/test_*.py`

**Three test types**:

1. **API tests** (`test_*_api.py`): HTTP-level with `AsyncClient` + `ASGITransport`. Use `ApiTestRunner` or
   `SimulatedAgentApiTestRunner`.
2. **Service unit tests** (`test_*_service_unit_tests.py`): Mocked NATS/DB via `patch.object` on entities.
3. **Integration tests** (`test_*_api_with_custom_event.py`): Full flow with `SimulatedAgentApiTestRunner` — simulates
   agent discovery responses and event handling over real NATS.

**Key classes**: `ApiTestRunner` (sync tests), `SimulatedAgentApiTestRunner` (async, simulates agents via NATS —
`.with_simple_chunk_events()`, `.create_agent_config_in_db()`, auto-responds to discovery requests).

**Auth bypass**: `DangerousDevelopmentOnlyAuthHandler` (auto-creates a dev identity).

**Interactive testing**: `cd playground/testing && python main.py` → http://localhost:8000 (frontend),
http://localhost:8000/api/v1/docs (Swagger).

**Pagination**: `PageNumber` and `PageSize` types in `pagination/`. Services return `tuple[int, list[DTO]]`.

## New Endpoint Workflow

1. Create DTOs in `routes/my_domain/dto/` (Pydantic v2, `from_entity()` factory, `in_locale(t)` if localized)
2. Create Service in `routes/my_domain/MyService.py` (`@staticmethod` + `@trace_fn`, call entities for persistence)
3. Create Controller in `routes/my_domain/MyController.py` (extend `Controller`, set `name`/`description` via
   `ApiLocaleString.from_i18n_path()`, `icon`, fluent methods returning `Self`)
4. Add translations in `i18n/translations/api/controllers.{de,en,fr,it}.yml`
5. Register in `app/main.py`: `runner.mount(MyController(auth=auth).method_a().method_b())`
6. Write tests in `playground/testing/tests/my_domain/`
7. Run `make test`

## Essential Files

- Production entry: `aihub_api/app/main.py`
- Controller base class: `aihub_lib/aihub_lib/routes/Controller.py`
- Example controller: `aihub_api/aihub_api/routes/agent/AgentController.py`
- Example service: `aihub_api/aihub_api/routes/agent/AgentService.py`
- Lifetime manager: `aihub_api/aihub_api/runners/lifetime/lifetime_manager.py`
- Agent discovery: `aihub_api/aihub_api/services/AgentEndpointsDiscoveryService.py`
- Model creation: `aihub_api/aihub_api/services/ModelCreationService.py`
- Event models: `aihub_api/aihub_api/events/EventModelCreationService.py`
- RPC responders: `aihub_api/aihub_api/rpc/AgentConfigResponder.py`
- WebSocket manager: `aihub_api/aihub_api/sockets/manager/WebSocketManager.py`
- i18n: `aihub_api/aihub_api/i18n/ApiLocaleString.py`, `ApiLocaleHandler.py`
- Test runner: `aihub_api/aihub_api/runners/simulation/agent/SimulatedAgentApiTestRunner.py`
- Playground: `aihub_api/playground/testing/main.py`
