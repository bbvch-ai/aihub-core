# Replace Arize Phoenix with Langfuse for LLM Observability

## Context

Swiss AI Hub uses an LLM observability platform for end-to-end agent tracing, cost monitoring, and evaluation
experiments. Previously, Arize Phoenix served this role for both tracing (via OpenTelemetry) and evaluations (via a
custom `PhoenixExperimentEvaluator`).

Phoenix is distributed under the **Elastic License 2.0 (ELv2)**, which explicitly prohibits providing the software as
part of a managed or SaaS offering. Swiss AI Hub ships as a turnkey Docker Compose stack that customers deploy as a
service — bundling Phoenix in this stack violates the ELv2 restriction. This licensing incompatibility forced an
immediate replacement regardless of technical considerations.

Beyond licensing, Phoenix had additional limitations: its experiment workflow required complex programmatic setup
tightly coupled to our NATS/ChatService infrastructure, cost tracking per model/user/agent was limited, and it is
primarily positioned as a development tool rather than a production observability platform.

Langfuse is an open-source (MIT-licensed) LLM observability platform that covers the same feature set — tracing, cost
tracking, dataset management, and experiment evaluation — without licensing constraints. It can be self-hosted, meeting
Swiss data sovereignty requirements.

## Decision Drivers

- **Elastic License 2.0 incompatibility**\
  Phoenix's ELv2 prohibits bundling within a SaaS or managed-service offering. Swiss AI Hub's Docker Compose
  distribution model breaches this restriction. Continuing to ship Phoenix exposes the project to legal risk.
- **MIT license compatibility**\
  Langfuse's MIT license has no restrictions on bundled, commercial, or SaaS deployment.
- **Production readiness**\
  Langfuse is built for production observability with authentication (Azure AD SSO), multi-tenancy, and scalability.
  Phoenix is primarily a development/debugging tool.
- **Native cost attribution**\
  Langfuse integrates with LiteLLM to track per-trace, per-user, and per-agent costs automatically. Phoenix required
  custom code for cost visibility.
- **UI-driven experiment workflow**\
  Langfuse provides built-in dataset management, experiment tracking, annotation tools, and scoring — replacing 850+
  lines of custom evaluation code (`PhoenixExperimentEvaluator`, `EvaluationController`, `EvaluationService`). By
  delegating experiment management to Langfuse's UI rather than rebuilding it ourselves, we automatically benefit from
  any features Langfuse adds in future releases without additional development effort.
- **OpenTelemetry compatibility**\
  Both Phoenix and Langfuse consume OpenTelemetry spans, so the tracing infrastructure (OTEL Collector, span
  instrumentation) remains unchanged. Only the exporter target changes.
- **Swiss data sovereignty**\
  Langfuse supports full self-hosted deployment via Docker Compose, keeping all trace and evaluation data on-premises.

## Decision

We replace Arize Phoenix with Langfuse across all environments and packages:

**Infrastructure**: Add Langfuse server, ClickHouse (analytics backend), and worker containers to Docker Compose.
Reconfigure the OpenTelemetry Collector to export OpenInference spans to Langfuse's OTEL ingestion endpoint with basic
auth instead of Phoenix.

**Auto-provisioning**: A `LangfuseProvisioner` runs on API startup to register Swiss AI Hub agents and LLM connections
in Langfuse. When agents come online, the `AgentEndpointsDiscoveryService` syncs them to Langfuse so they appear in the
experiment UI without manual configuration.

**Tracing**: `AgentRunTracer` enriches standard OTEL spans with `langfuse.*` span attributes (trace name, session, user,
input/output, usage details). These are the documented way to pass metadata to Langfuse's OTEL ingestion endpoint.
Regular OTEL consumers ignore them.

**Evaluations**: The programmatic experiment workflow (`PhoenixExperimentEvaluator`) is replaced by Langfuse's UI-driven
experiment workflow. Datasets are managed via the Swiss AI Hub API (`DatasetService`), experiments are created and run
in the Langfuse UI. A default prompt template maps dataset questions to agent requests.

**Frontend**: The custom experiment management UI (Create, Results pages) is removed. The dataset card links to the
corresponding Langfuse dataset page for experiment management.

## Consequences

### Positive

- No more licensing risk — MIT license is compatible with any distribution model
- Simplified codebase — removed 850+ lines of custom evaluation code
- Product owners and non-technical users can manage experiments via Langfuse UI without writing Python code
- Automatic cost tracking per trace, agent, and user enables budget optimization
- Zero-config experiment setup through auto-provisioning of agents and LLM connections
- Azure AD SSO integration provides proper access control for production deployments

### Trade-offs

- Loss of programmatic experiment API — experiments are now UI-driven. Langfuse Python SDK can restore programmatic
  access if needed later.
- Migration effort — 100 files changed across all packages. Changes follow project conventions and are well-structured.
- Additional Docker services (Langfuse, ClickHouse, worker) increase the deployment footprint.
- Cost tracking requires models that report per-token pricing (e.g. Azure OpenAI). Local models without cost metadata
  still work but won't show costs in Langfuse.
