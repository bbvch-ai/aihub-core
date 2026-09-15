# packages/api - REST API, WebSocket Gateway & MCP Server

**Purpose**: FastAPI REST API + WebSocket gateway + MCP server. Bridges frontends and external clients to Swiss AI Hub
services via the Swiss AI Agent Protocol.

## Scope Responsibility

HTTP endpoints, real-time WebSocket events, agent/process discovery, thread management, authentication enforcement,
protocol conversion (NATS events ↔ REST/WebSocket/SSE/OpenAI). NOT business logic — delegate to services.

## Folder Structure

```
packages/api/
├── app/main.py                 # Production entry — registers all controllers
├── swiss_ai_hub/api/
│   ├── routes/                 # Controllers + Services + DTOs (by domain)
│   │   ├── agent/              # Agent class/instance management
│   │   ├── thread/             # Conversation management
│   │   ├── user/               # User profiles, dashboards
│   │   ├── openai/             # OpenAI-compatible chat/embeddings/audio/images
│   │   ├── event/              # Event streaming + WebSocket endpoint
│   │   ├── process/            # Process orchestration
│   │   ├── knowledge/          # Vector DB / RAG operations
│   │   ├── memory/             # User & organization memory
│   │   ├── evaluation/         # Dataset & evaluation management
│   │   ├── role/               # Permission & role management
│   │   ├── tenant_admin/       # Sysadmin tenant metadata management (list/configure/update/delete tenants)
│   │   ├── file/               # File upload/download
│   │   ├── model/              # LLM model access
│   │   ├── notification/       # User notifications
│   │   ├── token/              # API token management
│   │   ├── translation/        # Translation service
│   │   ├── suite/              # Suite management
│   │   ├── health/             # Health & readiness checks
│   │   ├── i18n/               # Locale endpoints
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

`packages/api` serves dual purposes: it IS the production API, and it's an importable Python package. End-users can
import controllers from `swiss_ai_hub.api.routes.*`, mount them on an `ApiRunner`, and build custom APIs with any subset
of endpoints.

**Production API**: `app/main.py` registers all controllers and creates the app. New controllers MUST be registered
here, otherwise they won't be served. `runner.create_app()` also mounts an MCP server at `/mcp`, making the API
available as a Claude Code MCP tool for testing.

**Tenant-scoped routing**: Controllers extending `TenantScopedController` are mounted under `/api/v1/{tenant_id}/` and
include `{tenant_id}` as a path parameter in the OpenAPI spec (injected via a schema hook). The `{tenant_id}` is either
a concrete MongoDB ObjectId or `"active"` (resolves to the user's persisted active tenant). Global controllers extending
`Controller` directly (e.g., `MyTenantController`, `HealthController`, `TenantAdminController`) are mounted without a
tenant prefix. Three auth dependency patterns are available on the `Controller` base class:

- `user_with_permission(template)` — for tenant-scoped endpoints; checks the AccessChecker template against the acting
  tenant's rules.
- `authenticated_user()` — for global endpoints that any authenticated user may hit.
- `sys_admin_user()` — for sysadmin-only endpoints; gates on `UserIdentity.is_sys_admin` (the `AIHubSysAdmin` Keycloak
  realm role) and returns 403 otherwise. Used by `TenantAdminController`.

**Tenant states**: Tenants now have three observable states surfaced by `TenantAdminController` — **Active** (Keycloak
group + metadata), **Orphaned** (metadata-only, group missing), **Unconfigured** (group exists, no metadata). The
`TenantState` enum lives at `routes/tenant_admin/dto/tenant_state.py`. Attaching metadata to an Unconfigured group
("configure tenant") promotes it to Active and adds the Superuser as a member of the Keycloak group (per ADR
`2026_04_15_superuser_added_to_every_new_tenant`).

**Commands**: `make run-dev` (uvicorn with hot reload on :8000), `make run-prod` (gunicorn multi-worker).

**Docker**: `Dockerfile` builds the production image using `make run-prod` as entrypoint. End-users can also build their
own Docker image importing only the controllers they need.

## Controller-Service-DTO Pattern

**Controller** → HTTP endpoint definition, auth, routing. Fluent builder returning `Self`. **Service** → Business logic
with `@staticmethod` + `@trace_fn`. Stateless. Calls entities for persistence. **DTO** → Pydantic v2 models.
`@classmethod` factories (`from_entity()`, `from_discovery_event()`). `in_locale(t)` for localization. **Entity** →
MongoEngine documents with repository classmethods (lives in `packages/core/persistence/`).

Controllers must define class attributes: `name` and `description` via `ApiLocaleString.from_i18n_path()`, plus `icon`
(Iconify identifier). See `routes/agent/agent_controller.py` for the reference implementation.

Registration in `app/main.py`:

```python
runner.mount(MyController(auth=auth).create_resource().get_resource().delete_resource())
```

## FastAPI Dependencies

Custom dependencies injected via `Depends()` and `Security()` — use these in every endpoint:

| Dependency                                        | Provides                          | Source                                          |
| ------------------------------------------------- | --------------------------------- | ----------------------------------------------- |
| `Security(self.user_with_permission(template))`   | `UserIdentity` + permission check | `Controller` base class                         |
| `Depends(use_locale)` / `use_locale_ws`           | `ApiLocaleHandler` (i18n)         | `packages/api/i18n/dependencies/`               |
| `Depends(use_nats)` / `use_nats_ws`               | NATS client                       | `packages/core/swiss_ai_hub/core/dependencies/` |
| `Depends(use_external_agent_event_distributor)`   | Publish events to agents          | `packages/core/swiss_ai_hub/core/distributor/`  |
| `Depends(use_external_process_event_distributor)` | Publish events to processes       | `packages/core/swiss_ai_hub/core/distributor/`  |
| `Depends(use_s3)` / `use_s3_public`               | S3 client (internal / presigned)  | `packages/core/infrastructure/s3/`              |
| `Depends(use_milvus)`                             | Milvus vector DB client           | `packages/core/infrastructure/milvus/`          |
| `Depends(use_redis)`                              | Redis/Valkey client               | `packages/core/infrastructure/redis/`           |
| `Depends(use_vector_store_factory)`               | Vector store creation             | `packages/core/infrastructure/milvus/`          |
| `Depends(use_ws_manager)` / `use_ws_manager_ws`   | WebSocket connection manager      | `packages/api/sockets/`                         |

All infrastructure clients are initialized in `runners/lifetime/lifetime_manager.py` and stored in `app.state`.

## Error Responses

Services keep failing fast — they raise `HTTPException` for their own rejections (403, 404) and let everything else
propagate. What must not propagate out of the app is a model-gateway error: every LLM/STT/TTS/embedding call goes
through the OpenAI SDK, whose exceptions are not `HTTPException`, so unhandled they became Starlette's plain-text 500 —
no cause for the caller, and a span naming only the exception type, never the upstream message that says what to fix.

`ModelGatewayErrorHandler` (`packages/core/swiss_ai_hub/core/exceptions/model_gateway_error_handler.py`, registered once
in `Runner._get_api_app` so every service inherits it) translates them: it unwraps the upstream `error.message`, passes
through only the statuses a caller can act on (400/413/422/429) while mapping this deployment's own faults (401/403/404,
all 5xx) to 502 and upstream timeouts to 504. The response body carries the message under **both** `detail` and
`error.message` — platform clients read the former, the OpenAI-compatible clients this API emulates (OpenWebUI, OpenAI
SDKs) read only the latter.

Every one of these failures marks the current span `ERROR`. Handling the exception is what makes that necessary — it
never propagates out to the instrumentation's exception branch — and it deliberately includes the 4xx that OTel's
server-span convention would leave `UNSET`: passing an upstream status through means a 4xx here can just as well be a
model name this deployment got wrong. Log level is the narrower signal — `ERROR` with the traceback for what an operator
must fix, `WARNING` for the three statuses they cannot act on (413/422/429), which also keeps a rate-limit storm from
flooding the log pipeline.

New upstream integrations that raise their own SDK exception types belong in the same place — do not wrap service calls
in try/except to compensate.

**The one deliberate exception** is `OpenaiService.stt`, because one failure there is not a failure at all. The
transcription provider reports "I found no speech in this audio" as an HTTP 500 whose body reads
`Transcription failed: 0` — the `0` is a segment count, not a status. Measured against the provider on 2026-09-04:
silence, a 440 Hz tone and white noise all return it; 1.3 s of speech at -24 dBFS transcribes fine. So it is a verdict
on the audio, and it is the same verdict `AudioChunkingService.contains_speech` reaches locally for silence — where
this API already answers with an empty transcript, as OpenAI's own API does.

`stt` therefore catches exactly that classified cause (`ModelGatewayErrorHandler.is_untranscribable_audio`, never a
bare `APIStatusError`) and treats the chunk as holding no speech: it keeps the chunks that did transcribe, and returns
an empty transcript when none did. Everything else re-raises untouched — a misconfigured model or an expired key is not
a verdict on the audio, and answering it with an empty transcript would report "nobody spoke" for a deployment that
transcribes nothing. Two things make the silence recoverable afterwards, since a transcript quietly missing a passage is
worse than a failure: each such chunk logs the provider's verbatim message (it carries the upstream request id, the
only handle for asking the provider about it), and a summary logs how many of the recording's milliseconds are not in
the transcript.

`contains_speech` stays as a pre-filter rather than the whole answer: it detects sound at -40 dB, where the provider
detects speech, so tone and noise pass it and are rejected upstream.

## i18n System

**Hierarchy**: `LocaleString`/`LocaleHandler` (packages/core) → `ApiLocaleString`/`ApiLocaleHandler` (packages/api
extends with API-specific translation paths).

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

**Wildcards**: in a *rule*, `*` matches one token and `>` one or more trailing tokens. In a *template*, `?*` asks "any
rule with one more token here" and `?>` asks "any rule at or below this node" — a rule naming exactly that node
(`aihub.user.knowledge.db_a` vs `aihub.user.knowledge.db_a.?>`) satisfies it.

**Controller integration**: `Security(self.user_with_permission("aihub.user.agent.{agent_class}.?>"))` handles auth +
permission validation + OpenTelemetry span enrichment (user ID, email, roles, resource context) automatically.

**Service-level checks**: `AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id)` for fine-grained
authorization beyond endpoint-level permissions.

**Access capability catalog**: `AccessController` (`routes/access/`, served at `/access/capabilities` &
`/access/presets`) builds the human-readable capability table shown in the role and tenant-ceiling editors (and
read-only on the user page). It introspects each controller's routes at runtime and derives each capability's access
rule from the route's own `user_with_permission` guard — the single source of truth, never restated. To surface an
endpoint in the catalog, annotate its **fluent builder method** with
`@access_catalog_entry(i18n_path="api.access.capabilities.ops.<key>")` (the decorator lives in `api/decorators/`;
label/description only — the rule is derived). A guard containing `?` (`?>`/`?*`) has no single satisfying rule, so its
capability is read-only. The service gate (`aihub.user.service.X`) is synthesized from `service_name`; "Administer"
appears when an `aihub.admin.service.X` endpoint exists. The permission-string grammar (prefixes +
`agent_/process_/service_{user,admin}_rule` builders) lives on `AccessChecker`, not restated here. A curated plane
(sysadmin-api) that can't build the catalog locally subclasses `AccessController` and overrides the endpoints to proxy
them to the main API.

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

**DisplayEvents union** (`sockets/events/server_to_user/contextualized_agent_event.py`): The `DisplayEvents` type alias
is a discriminated union of all event types the WebSocket can serialize. The `event_discriminator` function walks
`_parent_event_names` to find the closest match in the union. **When adding a new subclass of any event type already in
the union, you MUST add the subclass to the `DisplayEvents` union too** — otherwise it silently downcasts to the parent
class during serialization, and the frontend echoes back the wrong type. See PR #1031 for the bug this caused with HITL
subtypes.

**Agents → API** (RPC): `AgentConfigResponder` and `ProcessConfigResponder` serve configuration data via NATS
request-reply on `aihub.rpc.config.agent.*.*` / `aihub.rpc.config.process.*.*`. Agents fetch their config at runtime
without needing it baked into event payloads.

**Protocol conversion**: WebSocket sends `ContextualizedAgentEvent` JSON. OpenAI-compatible SSE streams
`ChatCompletionChunk`. Aggregated endpoint collects events into `ChatCompletion` response.

## WebSocket

- Endpoint: `/api/v1/{tenant_id}/events/ws` (in `EventController`)
- Auth: First message must contain `{"token": "Bearer ..."}` — validated against auth handler
- Read-only from client: inbound messages after auth are ignored (security)
- Multi-connection per user: `WebSocketManager` tracks connections per user ID, syncs across tabs/devices
- Event routing: `WebSocketSender` finds thread participants via `ThreadEntity`, broadcasts to all their connections

## Lifetime Manager

`runners/lifetime/lifetime_manager.py` — FastAPI lifespan context manager wiring all infrastructure at startup.

**Startup order**: MongoDB → Redis/Milvus/S3 → NATS + JetStream → event persistence subscribers → WebSocket
infrastructure → event distributors → RPC responders → discovery services → DB initialization (default roles, knowledge
buckets) → cron scheduler → Langfuse provisioning.

All resources stored in `app.state`, accessible via the dependencies listed above.

**`CronScheduler`**: Fires cron-scheduled agent runs. Lives in `swiss_ai_hub.core.scheduling` and is only *wired* here —
it takes no FastAPI objects and registers no routes, so the move into `aihub-daemon` (#1203) is the dozen lines in
`lifetime_manager.py`, not a port. Correct across N replicas via a Redis leader lease; all its state (leadership, tick
watermark, per-occurrence claims, retention window) is in Redis and nowhere else. Tuned entirely through
`SchedulerSettings` (`SCHEDULER_*`), including `SCHEDULER_EVENT_RETENTION_DAYS`, which is **0 (off)** by default —
pruning a tenant's run history has to be switched on, never started by a deploy. Started *after*
`initialize_startup_tenant()` so a first tick cannot outrun tenant and role setup. Its Mongo reads all go through one
`asyncio.to_thread` hop per tick, because this process also serves every HTTP and WebSocket request.

A schedule's cost is checked when the profile is **saved**, not metered while it runs: `InstanceConfigHelper`
`.validate_cron_field` calls `ScheduleAdmission`, which computes how many runs the expression declares and rejects it
with a 400 if it passes `SCHEDULER_MAX_RUNS_PER_PROFILE_PER_MONTH` (default every-minute, so it refuses nothing
expressible) or `SCHEDULER_MAX_TOTAL_RUNS_PER_MONTH` across all profiles (default off). This bounds how *often* an agent
starts, not what it spends — that is #1766/#1767/#1452/#441. See ADR `2026_08_11_cron_scheduled_agent_runs` §9 for why
runtime metering was implemented and withdrawn.

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

**Auth bypass**: `TestAuthHandler` from `swiss_ai_hub.core.testing.auth_utils`. Returns the fixed test identity defined
in `core/testing/auth_utils/test_identity.py` (`TEST_USER_OID`, `TEST_USER_EMAIL`, `TEST_USER_ROLES`) and bypasses token
parsing. Lives under `core.testing` — not `core.auth` — so it is not reachable from production code.

**Interactive testing**: `cd playground/testing && python main.py` → http://localhost:8000 (frontend),
http://localhost:8000/api/v1/active/docs (Swagger).

**Pagination**: `PageNumber` and `PageSize` types in `pagination/`. Services return `tuple[int, list[DTO]]`.

## New Endpoint Workflow

1. Create DTOs in `routes/my_domain/dto/` (Pydantic v2, `from_entity()` factory, `in_locale(t)` if localized)
2. Create Service in `routes/my_domain/my_service.py` (`@staticmethod` + `@trace_fn`, call entities for persistence)
3. Create Controller in `routes/my_domain/my_controller.py` (extend `Controller`, set `name`/`description` via
   `ApiLocaleString.from_i18n_path()`, `icon`, fluent methods returning `Self`)
4. Add translations in `i18n/translations/api/controllers.{de,en,fr,it}.yml`
5. Register in `app/main.py`: `runner.mount(MyController(auth=auth).method_a().method_b())`
6. Write tests in `playground/testing/tests/my_domain/`
7. Run `make test`

## Essential Files

- Production entry: `packages/api/app/main.py`
- Controller base class: `packages/core/swiss_ai_hub/core/routes/controller.py`
- Example controller: `packages/api/swiss_ai_hub/api/routes/agent/agent_controller.py`
- Example service: `packages/api/swiss_ai_hub/api/routes/agent/agent_service.py`
- Lifetime manager: `packages/api/swiss_ai_hub/api/runners/lifetime/lifetime_manager.py`
- Agent discovery: `packages/api/swiss_ai_hub/api/services/agent_endpoints_discovery_service.py`
- Model creation: `packages/api/swiss_ai_hub/api/services/model_creation_service.py`
- Event models: `packages/api/swiss_ai_hub/api/events/event_model_creation_service.py`
- RPC responders: `packages/api/swiss_ai_hub/api/rpc/agent_config_responder.py`
- WebSocket manager: `packages/api/swiss_ai_hub/api/sockets/manager/web_socket_manager.py`
- DisplayEvents union: `packages/api/swiss_ai_hub/api/sockets/events/server_to_user/contextualized_agent_event.py`
- i18n: `packages/api/swiss_ai_hub/api/i18n/api_locale_string.py`, `api_locale_handler.py`
- Test runner: `packages/api/swiss_ai_hub/api/runners/simulation/agent/simulated_agent_api_test_runner.py`
- Playground: `packages/api/playground/testing/main.py`
