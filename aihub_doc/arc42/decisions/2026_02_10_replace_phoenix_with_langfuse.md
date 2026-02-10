# Replace Arize Phoenix with Langfuse for LLM Observability

**Status**: Accepted
**Date**: 2026-02-10
**Deciders**: AI-Hub Core Team
**Technical Story**: [PR #907](https://github.com/bbvch-ai/aihub-core/pull/907)

## Context and Problem Statement

AI-Hub requires comprehensive LLM observability and evaluation capabilities to:
- Trace agent execution flows end-to-end
- Monitor LLM performance and costs
- Evaluate agent quality through experiments
- Debug agent behavior in production

Previously, we used Arize Phoenix for observability and evaluation. However, as our platform matured, we identified limitations that necessitated a more robust solution.

## Decision Drivers

### Phoenix Limitations
1. **Experiment workflow**: Phoenix's experiment evaluation required complex programmatic setup (`PhoenixExperimentEvaluator`) with tight coupling to our NATS/ChatService infrastructure
2. **Cost tracking**: Limited visibility into per-model, per-user, and per-agent cost attribution
3. **Production readiness**: Phoenix is primarily positioned as a development/debugging tool, not a production observability platform
4. **Integration complexity**: Required custom code for dataset management, experiment execution, and result aggregation
5. **UI capabilities**: Less mature UI for managing experiments, datasets, and evaluation workflows

### Langfuse Advantages
1. **Industry-standard approach**: UI-driven experiment workflows align with how modern AI teams operate (similar to W&B, MLflow)
2. **Production-grade**: Built for production observability with proper authentication, multi-tenancy, and scalability
3. **Cost attribution**: Native support for cost tracking per trace, user, and session with LiteLLM integration
4. **Rich evaluation features**: Built-in dataset management, experiment tracking, annotation tools, and scoring workflows
5. **Active development**: Strong community, frequent updates, comprehensive documentation
6. **Self-hosted option**: Meets Swiss data sovereignty requirements with full Docker Compose deployment

### Migration Considerations
1. **LiteLLM model changes**: To enable Langfuse cost tracking, we migrated from local models (llama.cpp) to Azure OpenAI models across all tiers
   - Local models don't provide cost metadata that Langfuse can track
   - Azure OpenAI provides per-token cost data automatically captured by LiteLLM
   - This change enables accurate cost attribution per agent, user, and experiment
2. **Evaluation workflow shift**: Move from programmatic evaluation (`PhoenixExperimentEvaluator`) to UI-driven experiments in Langfuse
3. **Trace compatibility**: Both Phoenix and Langfuse consume OpenTelemetry spans, so tracing infrastructure remains unchanged

## Considered Options

### Option 1: Keep Phoenix, extend programmatic evaluation
**Pros**:
- No migration effort
- Team familiarity with existing codebase
- Programmatic API for CI/CD integration

**Cons**:
- Requires building custom UI for experiment management
- Limited cost tracking capabilities
- Phoenix not designed for production use
- Continued maintenance burden for custom evaluation code

### Option 2: Migrate to Langfuse (Selected)
**Pros**:
- Production-ready observability platform
- Native cost tracking with LiteLLM
- UI-driven experiment workflow (industry standard)
- Self-hosted deployment maintains data sovereignty
- Reduces custom evaluation code
- Active development and community support

**Cons**:
- Migration effort (100 files changed)
- Loss of programmatic experiment API (now UI-driven)
- Learning curve for team

### Option 3: Use Weights & Biases (W&B) or MLflow
**Pros**:
- Mature ML experiment tracking platforms
- Rich feature sets

**Cons**:
- Heavier infrastructure (not designed for real-time tracing)
- Less focus on LLM-specific observability
- W&B cloud-first (self-hosted option expensive)
- MLflow lacks native LLM tracing integration

## Decision Outcome

**Chosen option**: Migrate to Langfuse (Option 2)

Langfuse provides the best balance of production-readiness, LLM-specific features, cost tracking, and self-hosted deployment for Swiss data sovereignty requirements.

### Positive Consequences
- **Simplified codebase**: Removed 850+ lines of custom evaluation code (`PhoenixExperimentEvaluator`, `EvaluationController`, `EvaluationService`)
- **Better UX**: Product owners and non-technical users can manage experiments via Langfuse UI without writing Python code
- **Cost visibility**: Automatic cost tracking per trace, agent, and user enables budget optimization
- **Production observability**: Langfuse's authentication, multi-tenancy, and scalability support production deployments
- **Auto-provisioning**: `LangfuseProvisioner` automatically syncs discovered agents to Langfuse for zero-config experiment setup

### Negative Consequences / Trade-offs
1. **Loss of programmatic evaluation**: Previous `PhoenixExperimentEvaluator` allowed running experiments via API calls
   - **Mitigation**: Langfuse UI provides superior experiment management for most use cases
   - **Future option**: Langfuse Python SDK can be used if programmatic experiments are needed later
2. **Azure dependency for cost tracking**: Cost tracking requires Azure OpenAI (local models lack cost metadata)
   - **Mitigation**: Azure deployment is already standard for production; local models remain available for development without cost tracking
3. **Migration effort**: 100 files changed across all packages
   - **Mitigation**: Changes are well-structured and follow project conventions

## Implementation Details

### Infrastructure Changes
- **New services**: Added Langfuse server, ClickHouse (analytics backend), and worker containers to Docker Compose
- **OTEL pipeline**: Reconfigured OpenTelemetry Collector to export spans to Langfuse instead of Phoenix
- **Provisioning**: Added `LangfuseProvisioner` to automatically register AI-Hub agents and LLM connections in Langfuse on startup

### Code Changes
- **Deleted**: `PhoenixExperimentEvaluator` (264 lines), `EvaluationController` (195 lines), `EvaluationService` (395 lines)
- **Added**: `LangfuseProvisioner` (286 lines), `LangfuseSettings`, `LangfuseBootstrapSettings`, `DatasetService` (150 lines)
- **Refactored**: `AgentRunTracer` to set Langfuse-specific span attributes, `AgentEndpointsDiscoveryService` to sync agents to Langfuse

### Configuration Changes
- **LiteLLM**: Migrated from local models (gemma-3-4b via llama-cpp) to Azure OpenAI (gpt-5-nano, gpt-5-mini, etc.)
  - **Rationale**: Enable Langfuse cost tracking (local models don't provide cost metadata)
- **Environment variables**: Added 8 new Langfuse-specific variables (`.env.dev`, `.env.prod`)
- **OTEL**: Updated exporters to send traces to Langfuse endpoint with basic auth

### Frontend Changes
- **Removed**: Experiment management UI (131 lines in `Experiment/Create.vue`, 186 lines in `Experiment/Results.vue`)
- **Updated**: Dataset management UI redirects users to Langfuse for experiments
- **i18n**: Removed 31 experiment-related translation keys per locale

## Migration Path for Users

### For Developers
1. **Traces**: Existing traces automatically flow to Langfuse (OTEL compatible)
2. **Experiments**: Migrate from programmatic experiments to Langfuse UI:
   - Access Langfuse at http://localhost:6006 (dev) or configured production URL
   - Datasets managed via AI-Hub API remain compatible
   - Run experiments directly in Langfuse UI (see Langfuse docs)
3. **Cost tracking**: View per-trace costs in Langfuse dashboard (requires Azure OpenAI models)

### For Product Owners
- **Dataset management**: Continue using AI-Hub Admin UI (datasets page)
- **Experiment creation**: Use Langfuse UI instead of AI-Hub experiment page
- **Results analysis**: Langfuse provides richer visualization and annotation tools

### For Operations
- **Deployment**: Updated Docker Compose includes Langfuse services (no manual setup required)
- **Authentication**: Langfuse integrates with Azure AD SSO (configured via env vars)
- **Storage**: ClickHouse handles Langfuse analytics; SeaweedFS stores artifacts

## Links

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [OpenTelemetry Integration](https://langfuse.com/docs/integrations/opentelemetry)
- [PR #907: Replace Phoenix with Langfuse](https://github.com/bbvch-ai/aihub-core/pull/907)
- [Arize Phoenix Documentation](https://docs.arize.com/phoenix)
