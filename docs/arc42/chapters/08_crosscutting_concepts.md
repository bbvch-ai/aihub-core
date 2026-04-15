# Crosscutting concepts

This chapter describes design decisions and implementation patterns that apply across multiple building blocks. Each
concept appears in at least two packages or architectural layers and would be difficult to understand from any single
building block's documentation alone.

## Event system

...

## Form duality

The platform uses a pattern where a single Pydantic model serves two purposes depending on which values its fields hold.
In form mode, fields contain `FormkitElement` instances (subclasses of `PrimeVueElement`) that the Admin UI renders as
interactive form controls. In data mode, the same fields contain primitive Python values that agent code consumes at
runtime. The type system expresses this with union annotations: a field typed `float | InputNumber` holds either an
`InputNumber` form element or a `float` value.

## Authentication

Authentication uses a handler chain pattern. The abstract `AuthHandler` base class defines two methods: `__call__` for
standard HTTP requests and `authenticate_token` for WebSocket connections where the token arrives in the first message
payload rather than in HTTP headers. Concrete handlers extract and validate credentials, then delegate to an
`IdentityProvider` to resolve the full `UserIdentity` (ID, name, email, roles, profile image).

`KeycloakAuthHandler` validates Keycloak JWT tokens by fetching JWKS keys (cached 6 hours), verifying the RS256
signature, and checking audience and issuer claims. `TokenAuthHandler` validates API access tokens (format:
`sk-<url-safe-random>`) against MongoDB with direct indexed lookup and expiry checking. `OpenWebuiAuthHandler` verifies
HMAC-SHA256 signatures on OpenWebUI's custom headers (`X-OpenWebUI-User-Name`, `X-OpenWebUI-User-Email`,
`X-OpenWebUI-Signature`) before delegating to a wrapped inner handler. `DangerousDevelopmentOnlyAuthHandler` skips all
validation and returns a fake user identity for local development. The static superuser bearer token (`SUPERUSER_TOKEN`)
is materialized into the `bearer_tokens` collection at API startup, bound to the seeded Keycloak superuser, and
validated by `TokenAuthHandler` like any other bearer token — there is no dedicated superuser auth handler.

The production handler, `TokenAndOauth2Handler`, composes these strategies dynamically based on environment settings. It
tries OAuth2 handlers first (for browser-based SSO), then bearer token handlers (for API tokens and OpenWebUI pipeline
calls). The first handler that succeeds determines the user's identity.

After token validation, user data (name, email) is read from JWT claims for OAuth2 flows or fetched via
`KeycloakAdminService` for bearer tokens. No local user record is created — Keycloak is the sole store for user profile
data. The `AIHubSysAdmin` realm role carried on the JWT (or resolved via `KeycloakAdminService` for bearer tokens)
populates `UserIdentity.is_sys_admin`, which short-circuits `AccessChecker.access_level()` to `ACCESS_ADMIN` for
platform administrators.

## Authorization

Authorization uses a hierarchical rule-based model. Each role (stored as a `RoleEntity` in MongoDB) contains a list of
access rules in dotted-path notation. Rules follow the pattern `aihub.[user|admin].<resource>.<subresource>.<id>`, where
`*` matches any single segment and `>` matches one or more trailing segments. An admin rule (`aihub.admin.agent.>`)
implicitly grants user-level access as well.

Permission checks happen at three levels in the `Controller.user_with_permission()` dependency. First, the controller
verifies that the user has access to the controller's service (`has_access_to_service()`). Second, it checks any
additional controller-level permission. Third, it checks the resource-level permission with path parameters interpolated
into the template (e.g., `aihub.user.agent.{agent_class}.{agent_id}` becomes `aihub.user.agent.RAGAgent.hr-agent`). All
three checks must pass; failure at any level returns HTTP 403.

Thread-level access control uses participant lists stored on `ThreadEntity`. The `WebSocketSender` checks thread
participants before forwarding display events, and the `ExternalAgentEventDistributor` verifies that the user belongs to
the thread before publishing events.

Role-based rate limiting supplements RBAC. Each role can define usage limits with patterns, counts, and time periods (1
hour, 1 day, 7 days, 1 month). The `UsageLimits` class uses a Redis Lua script for atomic check-and-increment operations
and returns HTTP 429 with localized error messages when limits are exceeded. .

## Internationalization

All user-facing strings support four languages: German, English, French, and Italian. The `LocaleString` Pydantic model
stores one string per language (`de`, `en`, `fr`, `it` fields) and resolves to a single string via `in_locale()`.
`LocaleHandler` manages runtime locale resolution with a fallback chain: requested locale, then the default locale
(German), then the first available translation.

Translation files are YAML-based, organized by scope and topic: `lib/agents.de.yml`, `bot/error.fr.yml`,
`api/controllers.en.yml`. Keys use dot notation (`lib.events.start_event.name`). A test enforces that every YAML file
exists in all four locale variants.

Locale resolution in the API follows a priority order. The `I18nMiddleware` checks the `lang` header, then the `locale`
header, then `Accept-Language`, then path parameters, then query parameters, and finally falls back to German. The
resolved locale is stored in `request.state.locale` and injected into endpoints via `Depends(use_locale)`.

Display events carry localized display names and descriptions as `ClassVar[LocaleString]` on the event class. The
`WebSocketSender` resolves these to the user's locale when wrapping events in `ContextualizedAgentEvent` for WebSocket
delivery. Controller classes define their `name` and `description` as `LocaleString` instances loaded from translation
files.

The form system integrates with i18n through `PrimeVueElement.in_locale()`, which resolves `LocaleString` labels and
help text to a single string for the current locale and appends ` *` to required field labels. The `LocaleInput` form
element provides a four-field editor for entering translations directly in the Admin UI.

## Observability

The platform's observability stack combines OpenTelemetry for distributed tracing with Langfuse for AI-specific
monitoring. Both consume the same trace data through different pipelines.

`SmartTracer` wraps the standard OpenTelemetry tracer with two additions: a `@trace_fn` decorator that automatically
captures function parameters, return values, and exceptions as span attributes, and a `@no_trace` decorator that
suppresses all tracing for a function and its sub-calls (used for health checks and high-frequency internal operations).
`SmartTracerProvider` respects the `suppress_instrumentation` context by returning non-recording spans, allowing trace
suppression to propagate through the call tree.

Trace context propagation across NATS boundaries uses W3C Trace Context headers. `NATSTraceContextPropagator` injects
the current span context into NATS message headers on publish and extracts it on receive. Every
`JSPublisher.publish_event()` call creates a span with semantic messaging attributes (`messaging.system`,
`messaging.destination`, `messaging.operation`) and injects trace context into the message headers. On the subscriber
side, `JSSubscriber` extracts the trace context before dispatching to the handler, creating a continuous trace from HTTP
request through NATS to agent step execution.

The OTEL Collector serves as the central telemetry hub. It receives traces from all instrumented services via OTLP (gRPC
on port 4317, HTTP on port 4318) and routes them through two processing pipelines. A noise filter drops health check
spans, database client spans, and LiteLLM internal spans. A Langfuse filter selects only spans carrying the
`openinference.span.kind` attribute (semantic AI events: LLM calls, retrieval operations, guard evaluations) and
forwards them to Langfuse's OTLP endpoint. Optionally, unfiltered traces are exported to an external observability
backend (SigNoz, Datadog, Grafana Cloud) configured via environment variables.

LiteLLM emits OpenInference-compatible spans for every LLM call via its built-in OTEL callback. These spans carry token
counts, model names, and cost data, which Langfuse uses for per-user and per-agent cost attribution. The
`LangfuseProvisioner` runs at API startup to register LLM connections, custom model pricing definitions (since model
names like `text-generation/gpt-oss-120b` do not match Langfuse's built-in pricing database), and default prompt
templates.

Controllers enrich HTTP spans with authorization context: user ID, email, roles, service name, required permission,
agent class, and thread ID. This connects the HTTP layer's observability with the downstream NATS event traces.

## License compliance

The platform enforces license compliance through a three-layer CI check that runs on every pull request. The
`generate-license.sh` script scans Python packages (via `pip-licenses`), Node.js packages (via `pnpm licenses`), and
Docker images (parsed from all compose files) against a classification in `licenses.config.json`. Restrictive licenses
(GPL, AGPL, SSPL, OSL-3.0, EUPL) fail the build. Permissive licenses (MIT, Apache, BSD, ISC, PSF, MPL) pass
automatically. Licenses requiring review (EPL, CDDL, CC-BY-SA) must be explicitly approved.

The license checker maintains an override list for packages where `pip-licenses` reports incorrect metadata. Neo4j
Community Edition (GPL) is manually approved because it runs as a separate container, not as a linked library.

## Error handling

The platform follows a fail-fast exception propagation strategy. Agent steps do not catch exceptions defensively; errors
propagate to the dispatcher, which decides the response based on the step's `stop_on_error` flag.

When `stop_on_error` is true (the default), the dispatcher publishes an `ExceptionEvent` carrying the error message and
an HTTP status code. Because `ExceptionEvent` is both a control event and a display event, a single publication achieves
two effects: as a control event on JetStream, it reaches the dispatcher's own `handle_event()` method, which marks the
run as crashed in Valkey's `StepStore` and prevents any further step execution for that run. As a display event on NATS
Core, it reaches the WebSocket sender and the SSE generator, which surface the error to the user and close the response
stream.

When `stop_on_error` is false, the step fails silently. The exception is logged and traced, but the run continues. Other
steps that do not depend on the failed step's output can still execute. This option is used for optional enrichment
steps where failure should not block the primary workflow.

The `StepStore.is_execution_context_crashed()` check runs before every step execution. Once a run is marked as crashed,
the flag persists in Valkey and survives agent restarts, preventing any attempt to resume a failed run.

## Testing

Agent tests use BDD with pytest-bdd for workflow scenarios and plain pytest for unit tests. Feature files (Gherkin) in
`tests/features/` define scenarios in natural language; step implementations in `test_*.py` files map Given/When/Then
clauses to Python code. An `@async_test` decorator bridges async step implementations into synchronous pytest-bdd by
wrapping them in `asyncio.run()`.

## Generated TypeScript SDK

The frontend's API client is generated from the FastAPI server's OpenAPI schema using HeyAPI (`@hey-api/openapi-ts`).
The generator reads the live schema from `http://localhost:8000/api/v1/active/openapi.json` and produces type
definitions, SDK functions (one per endpoint), JSON schemas, and response transformers (for date coercion) into
`sdk/client/`. The `@hey-api/client-nuxt` plugin configures the generated client to use Nuxt's `$fetch` composable for
SSR-compatible cookie and header forwarding.

Because agent endpoints are registered dynamically at runtime (see chapter 6 (Runtime view), agent discovery), the
generated SDK's type coverage extends to agent-specific request and response types. When a new agent class is discovered
and its endpoints are registered, regenerating the SDK (`pnpm generate-sdk`) picks up the new endpoint types
automatically.

The generated files are committed to the repository. The frontend's event display components use a resolution function
that maps `_event_name` to Vue components, walking `_parent_event_names` for inheritance-based fallback when the
specific event type has no dedicated component.
