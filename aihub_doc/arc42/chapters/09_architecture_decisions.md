# Architecture decisions

Architecture decisions are recorded as ADRs in `aihub_doc/arc42/decisions/`. Each ADR follows the format
`YYYY_MM_DD_short-kebab-summary.md` with Context, Decision Drivers, Decision, and Consequences sections. Reversing an
existing ADR requires a new ADR justifying the change.

This chapter summarizes all recorded decisions grouped by concern. The full rationale, alternatives considered, and
detailed consequences are in the individual ADR files.

## Infrastructure and deployment

### Containerized multi-environment deployment (2025-08-11)

The platform deploys as Docker Compose files generated for multiple environments (dev, local, build, nightly, latest)
with optional GPU variants. Each AI-Hub scope gets its own containerized application. This decision traded operational
simplicity (single-command deployment, environment-specific resource allocation) against maintenance overhead from
multiple compose files and significant local resource requirements. The Jinja2 template system described in chapter 7
(Deployment view) was introduced later to mitigate the maintenance cost.

### Docker network isolation (2025-12-22)

All containers originally ran in a single flat network. This decision introduced five isolated Docker networks (proxy,
backend, data, storage, egress) based on the principle of least-privilege networking. Services are assigned only the
networks they require. The egress network disables inter-container communication entirely, restricting Playwright to
outbound internet access without lateral movement capability. The trade-off is that network assignments must be
explicitly maintained when adding new services.

### Pulumi as infrastructure-as-code framework (2024-12-18)

Pulumi was adopted for managing cloud infrastructure using Python, keeping the IaC language consistent with the rest of
the project. The main trade-off is that Pulumi manages its own state, which must be persisted and kept in sync with
actual infrastructure to avoid drift.

### Component-specific CI/CD build pipelines (2025-08-11)

The monolithic build process was replaced with component-specific GitHub Actions workflows. Each scope (API, bot,
agents, pipelines, web, Dagster) has its own build workflow, coordinated via `repository_dispatch` events. Agent
discovery in CI is dynamic: the build workflow parses `compose-config.yml` to find all agent entries, so adding a new
agent to the configuration file is sufficient to include it in the pipeline. The trade-off is multiple workflows to
maintain and complex version coordination across components.

## Observability and tracing

### OpenTelemetry for end-to-end distributed tracing (2025-09-15)

The event-driven architecture created a visibility gap across NATS message boundaries. This decision introduced W3C
Trace Context propagation through NATS message headers, named publishers and subscribers for identifiable spans, and
automatic instrumentation in base classes. All publishers and subscribers must carry meaningful names. The decision
originally used Phoenix as the visualization backend; the subsequent Langfuse migration (2026-02-10) changed only the
exporter target.

### Replace Arize Phoenix with Langfuse (2026-02-10)

Phoenix's Elastic License 2.0 prohibits bundling within a managed service offering, which the platform's Docker Compose
distribution model constitutes. This licensing incompatibility forced an immediate replacement. Langfuse (MIT license)
was chosen because it provides native cost attribution via its LiteLLM integration, a UI-driven experiment workflow that
replaced approximately 850 lines of custom evaluation code, Azure AD SSO support, and full self-hosted deployment for
Swiss data sovereignty compliance. The migration required changes across approximately 100 files but simplified the
codebase overall. The trade-off is the loss of Phoenix's programmatic experiment API and the addition of three Docker
services (Langfuse web, Langfuse worker, ClickHouse).

## Agent runtime and configuration

### Dynamic agent configuration through Admin UI (2026-01-07)

Changing agent behavior originally required code changes and redeployment. This decision introduced the form duality
pattern: a single Pydantic model serves as both the UI form schema (fields hold FormKit elements) and the runtime data
model (fields hold primitive values). Administrators create agent profiles through the Admin UI without developer
involvement. The trade-off is that agents must implement `as_form()` and use type unions for configurable fields, and
schema evolution can leave stale persisted configurations in the database.

### Agent profile templates (2026-02-17)

After removing the legacy default configuration mechanism, new agents required full manual profile creation. An initial
approach that auto-created profiles during discovery was rejected because it silently materialized database state, could
create orphaned profiles, and could not represent multiple valid starting configurations. The adopted solution uses
profile templates: predefined data-mode `AgentConfig` instances declared in Python and transmitted during discovery. The
Admin UI presents template selection when creating profiles, prefilling form fields with two clicks. Templates never
auto-create profiles; an admin action is always required. The intentional trade-off is that agents do not work
immediately after deployment until an administrator creates at least one profile.

### Adopt mem0 for agent memory (2025-12-18)

Agents operated statelessly, with each conversation starting fresh. This decision introduced a dual-scope, dual-storage
memory architecture using mem0. User memory is private and LLM-inferred from conversations, stored in vector storage for
agent-specific preferences and in Neo4j for shared factual knowledge. Organization memory is per-tenant, explicitly
provided, and shared across users. The trade-off is increased operational complexity (Neo4j added to the stack),
additional LLM cost for memory extraction, and the need for a memory management UI to support GDPR deletion
requirements.

## Document processing

### Adopt MinerU for document parsing (2026-02-09)

Docling was the original document parser but faced scalability problems: pipeline mode took minutes per page on CPU, and
VLM mode with remote granite-docling degraded quality. MinerU replaced Docling entirely, using VLM-only mode with the
MinerU2.5-2509-1.2B model. The architecture runs `mineru-api` as a CPU-only container that routes VLM inference through
LiteLLM, and optionally `mineru-vlm` as a GPU container via vLLM. Processing speed improved 4-10x over Docling. MinerU's
AGPL license is managed through strict network isolation: no Python imports from MinerU exist in any platform package,
and communication happens exclusively via REST API. The trade-off is dependency on a partner-hosted VLM endpoint for
CPU-only deployments and two additional containers in the stack.

## Frontend integration

### SSE for OpenWebUI integration (2025-08-27)

OpenWebUI's OpenAI-compatible endpoints only streamed plain text, unable to communicate the platform's rich event system
(ThoughtEvent, ToolEvent, HumanInTheLoopRequestEvent). This decision introduced SSE streaming endpoints alongside the
existing WebSocket infrastructure. SSE carries structured event payloads over unidirectional HTTP connections, which are
compatible with proxies and load balancers and auto-close when the agent completes. WebSocket remains for bidirectional
Admin UI communication. The trade-off is maintaining two concurrent streaming mechanisms in the API.

### Dual OpenWebUI pipelines (2025-09-02)

AI agents (complex workflows with rich events) and LLM models (simple text generation) represent fundamentally different
use cases. A single pipeline would either oversimplify agent interactions or overcomplicate model access. This decision
introduced two separate OpenWebUI pipelines: an event-based agent pipeline with full event processing and OpenWebUI
feature integration (thinking indicators, tool status, citations), and an OpenAI-compatible model pipeline that passes
requests directly to LiteLLM without event processing. The trade-off is two codebases to maintain and a user-facing
distinction between pipeline types.

## Security and authentication

### Global superuser authentication (2025-08-11)

Two authentication gaps existed: external services in Docker Compose had no way to authenticate out of the box, and
customers deploying the platform as a pure backend without an identity provider had no viable authentication option.
This decision introduced a global superuser with a `SUPERUSER_TOKEN` environment variable, configurable via
`SUPERUSER_ENABLED`. The superuser bypasses RBAC and is used internally by the `LangfuseProvisioner` for startup
provisioning. The trade-off is that the single global token is a high-value attack target and risks being overused
instead of proper per-service authentication.

## Developer experience

### MCP protocol for AI-assisted development (2025-07-09)

AI coding assistants worked in isolation without access to the live development environment. This decision adopted a
two-pronged MCP strategy: configuring AI coding assistants with MCP servers for database access, observability, and API
interaction, and implementing MCP server capabilities directly in the AI-Hub API (exposing read-only GET endpoints at
`/mcp`). The trade-off is added complexity, Docker dependency for MCP servers, and security considerations around giving
AI assistants access to production-like data.

### Claude Code enablement (2026-02-11)

The monorepo had basic AI-assisted development support but was not leveraging modern Claude Code features. This decision
introduced comprehensive Claude Code configuration: project-level hooks for auto-formatting, sensitive file protection,
scope boundary checking, and git hygiene; skills for component scaffolding and developer workflows; custom subagents
with project memory for specialized tasks; and enhanced MCP server integration. All configuration is version-controlled
in the repository. The trade-off is that hook definitions and subagent configurations require maintenance as the
codebase evolves.

## Other decisions

### LLM-based whitepaper generation (2025-12-05)

Technical documentation needed to be transformed into business-focused whitepaper content for decision-makers. This
decision introduced an iterative Python-based LLM generator with chapter-centric folder organization, sequential chapter
generation (passing prior chapters as context for terminology consistency), and LaTeX/PDF output. The process is
manually triggered, not automatic, to control LLM API costs. The trade-off is non-deterministic source discovery and a
5-10 minute generation cycle.
