# Crosscutting concepts

This chapter describes design decisions and implementation patterns that apply across multiple building blocks. Each
concept appears in at least two packages or architectural layers and would be difficult to understand from any single
building block's documentation alone.

## Event system

The Swiss AI Agent Protocol defines a typed event hierarchy rooted in `BaseEvent`. Every event subclass self-registers
in a class-level registry via `__pydantic_init_subclass__` at import time. This registry enables polymorphic
deserialization: `BaseEvent.deserialize_event(data)` looks up the `_event_name` field in the registry and instantiates
the correct subclass. If the exact class is unknown (the receiving code does not have that event's module imported), the
deserializer walks `_parent_event_names` until it finds a known ancestor, preserving forward compatibility when agents
publish event types that the API has never seen.

The hierarchy branches into three categories. `ControlEvent` drives workflow state transitions. Only control events
trigger step execution in the dispatcher, and they are published to NATS JetStream for durable delivery. `DisplayEvent`
provides observability data for frontends and tracing systems. Display events are published to NATS Core for ephemeral
real-time delivery; losing them does not affect workflow correctness. `ControlAndDisplayEvent` serves both purposes
simultaneously and is the most common base class for concrete events. `StartEvent`, `StopEvent`,
`HumanInTheLoopRequestEvent`, and `ExceptionEvent` are all control-and-display events because they drive workflow
transitions and are visible in the UI.

`SemanticEvent` extends `ControlAndDisplayEvent` with an abstract `to_semantic_convention()` method that returns
OpenInference-compatible attribute dictionaries. `LLMEvent`, `RetrieverEvent`, `EmbeddingEvent`, `RerankerEvent`,
`GuardEvent`, and `ExceptionEvent` are semantic events. This makes them simultaneously NATS workflow events (consumed by
dispatchers and frontends) and OpenTelemetry trace data (exported to Langfuse for AI-specific observability). A single
event publication serves both the workflow engine and the observability pipeline.

NATS subjects encode routing and scoping information directly in the topic string. Agent subjects follow the pattern
`agent.{class}.{id}.{thread}.{display}.{run}.{event_type}.{event_name}.{event_id}`, where `event_type` is either
`control_event` or `display_event`. Process subjects follow
`process.{class}.{id}.{walkthrough}.{event_type}.{event_name}.{event_id}`. `TopicManager` classes build these subjects
programmatically, and `Topic.from_subject()` parses them back using the same auto-registration pattern as events.

The three scope levels in agent topics serve different purposes. `thread_id` identifies a user's conversation and
persists across multiple agent runs. `display_id` groups what the UI should render together within one logical
interaction. `run_id` identifies a single agent execution and serves as the `execution_context_id` for step tracking,
event replay, and crash recovery.

## Form duality

The platform uses a pattern where a single Pydantic model serves two purposes depending on which values its fields hold.
In form mode, fields contain `FormkitElement` instances (subclasses of `PrimeVueElement`) that the Admin UI renders as
interactive form controls. In data mode, the same fields contain primitive Python values that agent code consumes at
runtime. The type system expresses this with union annotations: a field typed `float | InputNumber` holds either an
`InputNumber` form element or a `float` value.

The `Form` base class provides methods for both modes. `to_formkit_form()` recursively extracts `FormkitElement`
instances from the model's fields and produces a list of form element definitions for the frontend. Nested `Form`
subclasses become `Group` elements; `list[Form]` fields become `Repeater` elements. `to_form_submission_model()` strips
the `FormkitElement` types from all union annotations and returns a pure-primitives Pydantic model that the API uses to
validate form submissions. `to_configurable_submission_model()` is instance-based: it only includes fields that
currently hold `FormkitElement` values, producing a schema that reflects which fields are configurable for a specific
agent instance.

The distinction between configurable and non-configurable fields is determined by the `as_form()` class method. Fields
set to `FormkitElement` instances are configurable (the user edits them in the Admin UI). Fields set to primitive values
are non-configurable (baked into the agent code, invisible to the UI). At runtime, `deep_merge()` combines the
non-configurable values with the user-submitted configuration, and `model_validate()` reconstructs the typed config
object in data mode.

Three normalization functions handle FormKit's serialization quirks. `transform_formkit_arrays()` converts FormKit's
numeric-keyed object encoding (`{"0": {...}, "1": {...}}`) back to Python lists. `normalize_empty_objects_to_none()`
converts empty dicts (sent by FormKit for disabled nested forms) to `None`. `normalize_empty_locale_strings()` converts
locale dicts where all values are empty strings to `None`.

Twenty-eight concrete `PrimeVueElement` subclasses cover the standard form controls: text inputs, number inputs,
checkboxes, toggles, selects, multi-selects, date pickers, sliders, and domain-specific elements like `ModelSelect` (LLM
model chooser), `KnowledgeDatabaseSelector` (vector store namespace picker), and `LocaleInput` (four-language string
editor).

## Authentication

Authentication uses a handler chain pattern. The abstract `AuthHandler` base class defines two methods: `__call__` for
standard HTTP requests and `authenticate_token` for WebSocket connections where the token arrives in the first message
payload rather than in HTTP headers. Concrete handlers extract and validate credentials, then delegate to an
`IdentityProvider` to resolve the full `UserIdentity` (ID, name, email, roles, profile image).

Seven handler implementations exist. `OAuth2AuthHandler` validates Azure AD JWT tokens by fetching JWKS keys (cached 6
hours), verifying the RS256 signature, and checking audience and issuer claims. `TokenAuthHandler` validates API access
tokens (format: `{ObjectId}.{128-char-random}`) against MongoDB with constant-time comparison and expiry checking.
`OpenWebuiAuthHandler` verifies HMAC-SHA256 signatures on OpenWebUI's custom headers (`X-OpenWebUI-User-Name`,
`X-OpenWebUI-User-Email`, `X-OpenWebUI-Signature`) before delegating to a wrapped inner handler. `SuperuserAuthHandler`
compares bearer tokens against a hardcoded environment variable for service-to-service authentication.
`DangerousDevelopmentOnlyAuthHandler` skips all validation and returns a fake user identity for local development.

The production handler, `TokenAndOauth2Handler`, composes these strategies dynamically based on environment settings. It
tries OAuth2 handlers first (for browser-based SSO), then bearer token handlers (for API tokens, OpenWebUI pipeline
calls, and superuser access). The first handler that succeeds determines the user's identity.

After token validation extracts the user's Azure AD object ID, `AzureIdentityProvider` concurrently fetches the user
profile, app role assignments, and profile image from the Microsoft Graph API (all cached with TTL). On first login,
`UserEntity.ensure_user_exists()` creates a local user record in MongoDB.

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
and returns HTTP 429 with localized error messages when limits are exceeded.

## PII detection

PII detection and anonymization is implemented as LiteLLM pre-call guardrails using Microsoft Presidio. Two guardrails
are configured: `presidio-mask-guard` replaces detected entities (person names, email addresses) with tokens like
`<PERSON>`, and `presidio-block-guard` rejects requests entirely if certain entity types (credit card numbers) are
detected. Both run in `pre_call` mode, intercepting prompts before they reach any LLM provider. The `output_parse_pii`
option also scans model responses before returning them to the caller.

Guardrails are not enabled by default. Agent code must explicitly include guardrail names in the LiteLLM request
metadata (`metadata.guardrails: ["presidio-mask-guard"]`) to activate PII filtering for a specific call. This allows
agents that work exclusively with local models (where data never leaves the infrastructure) to skip the overhead, while
agents that route to external providers can enforce PII masking.

Presidio runs as two separate microservices (analyzer for NER detection, anonymizer for text replacement) on the backend
network. The analyzer uses NER models configured for German by default, with language selection per guardrail.

LiteLLM additionally runs prompt injection detection as a callback, using both pattern-based similarity checking against
known attack patterns and an LLM-based classifier that evaluates prompts for malicious intent.

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
the current span context into NATS message headers on publish and extracts it on receive. `NATSMessageHeaders` provides
a fluent builder: `.with_trace_context().with_header("Nats-Msg-Id", id).to_dict()`. Every `JSPublisher.publish_event()`
call creates a span with semantic messaging attributes (`messaging.system`, `messaging.destination`,
`messaging.operation`) and injects trace context into the message headers. On the subscriber side, `JSSubscriber`
extracts the trace context before dispatching to the handler, creating a continuous trace from HTTP request through NATS
to agent step execution.

The OTEL Collector serves as the central telemetry hub. It receives traces from all instrumented services via OTLP (gRPC
on port 4317, HTTP on port 4318) and routes them through two processing pipelines. A noise filter drops health check
spans, database client spans, and LiteLLM internal spans. A Langfuse filter selects only spans carrying the
`openinference.span.kind` attribute (semantic AI events: LLM calls, retrieval operations, guard evaluations) and
forwards them to Langfuse's OTLP endpoint. Optionally, unfiltered traces are exported to an external observability
backend (SigNoz, Datadog, Grafana Cloud) configured via environment variables.

LiteLLM emits OpenInference-compatible spans for every LLM call via its built-in OTEL callback. These spans carry token
counts, model names, and cost data, which Langfuse uses for per-user and per-agent cost attribution. The
`LangfuseProvisioner` runs at API startup to register LLM connections, custom model pricing definitions (since model
names like `text-generation/nano` do not match Langfuse's built-in pricing database), and default prompt templates.

Controllers enrich HTTP spans with authorization context: user ID, email, roles, service name, required permission,
agent class, and thread ID. This connects the HTTP layer's observability with the downstream NATS event traces.

## License compliance

The platform enforces license compliance through a three-layer CI check that runs on every pull request. The
`generate-license.sh` script scans Python packages (via `pip-licenses`), Node.js packages (via `pnpm licenses`), and
Docker images (parsed from all compose files) against a classification in `licenses.config.json`. Restrictive licenses
(GPL, AGPL, SSPL, OSL-3.0, EUPL) fail the build. Permissive licenses (MIT, Apache, BSD, ISC, PSF, MPL) pass
automatically. Licenses requiring review (EPL, CDDL, CC-BY-SA) must be explicitly approved.

Three license-driven technology decisions shape the architecture. MinerU (AGPL) runs in isolated Docker containers with
REST-only communication; no Python imports from MinerU exist in any platform package, maintaining the AGPL license
boundary. Valkey replaced Redis after Redis changed its license to RSALv2/SSPL, which conflicts with the platform's
distribution as a bundled Docker Compose stack. Langfuse (MIT) replaced Arize Phoenix (Elastic License 2.0) because ELv2
prohibits bundling within a managed service offering.

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

`AgentTestRunner` extends `AgentRunner` with test-specific behavior. It mocks the configuration RPC client (returning
the test's `agent_config.model_dump()` directly, no API server needed) and subscribes to all events published during the
test run, collecting them in an `observed_events` list. The `test_run()` async context manager starts the runner,
generates fresh scope IDs (thread, display, run), yields a topic for sending events, and polls for a `StopEvent` before
teardown. Assertion helpers (`has_event_of_class`, `get_events_of_class`, `wait_for_event`) provide a fluent API for
verifying workflow outcomes.

Dispatcher unit tests use a different approach: stateful in-memory mock Redis, mocked NATS clients, and real dispatcher
instances with controlled step readiness via `patch.object`. This tests the dispatcher's routing and error handling
logic without requiring running infrastructure.

Test markers (`slow`, `azure`, `integration`, `flaky`, `self_hosted`, `experimental`) are defined in per-scope
`pyproject.toml` files. CI runs `pytest -m "not azure and not flaky"` to exclude tests that require external services or
have known stability issues.

## Generated TypeScript SDK

The frontend's API client is generated from the FastAPI server's OpenAPI schema using HeyAPI (`@hey-api/openapi-ts`).
The generator reads the live schema from `http://localhost:8000/api/v1/openapi.json` and produces type definitions, SDK
functions (one per endpoint), JSON schemas, and response transformers (for date coercion) into `sdk/client/`. The
`@hey-api/client-nuxt` plugin configures the generated client to use Nuxt's `$fetch` composable for SSR-compatible
cookie and header forwarding.

Because agent endpoints are registered dynamically at runtime (see chapter 6 (Runtime view), agent discovery), the
generated SDK's type coverage extends to agent-specific request and response types. When a new agent class is discovered
and its endpoints are registered, regenerating the SDK (`pnpm generate-sdk`) picks up the new endpoint types
automatically.

The generated files are committed to the repository. The frontend's event display components use a resolution function
that maps `_event_name` to Vue components, walking `_parent_event_names` for inheritance-based fallback when the
specific event type has no dedicated component.
