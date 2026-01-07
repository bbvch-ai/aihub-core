# Enable Dynamic Agent Configuration Through Admin UI

## Context

The AI-Hub platform supports multiple agent types (RAG agents, specialized assistants, etc.) that each have runtime
configuration requirements. Previously, modifying agent behavior required:

- **Code Changes**: Developers had to modify `AgentConfig` classes and redeploy services to change configuration values.
- **Technical Barrier**: Non-technical users (administrators, business analysts) could not customize agent behavior to
  meet specific use cases without developer involvement.

While agents already had a configuration system through Pydantic-based `AgentConfig` classes, there was no way to expose
these configurations to end users through the UI or to persist user-customized configurations separately from the
default values.

## Decision Drivers

- **User Self-Service**: Enable administrators and business users to customize agent configurations without code changes
  or developer involvement.
- **Type Safety Preservation**: Configuration changes should still be validated against the agent's expected schema,
  preventing invalid configurations.

## Decision

We will implement dynamic agent configuration through the Admin UI using the following approach:

1. **Explicit Form Definitions**: Agents define FormKit form elements separately from their `AgentConfig` Pydantic
   model. Form elements are passed explicitly to `AgentConfigSpecs.from_agent_config()` and included in agent discovery
   responses. This separation keeps configuration data (Pydantic) and UI presentation (FormKit) cleanly decoupled.

2. **Store Configuration Specs with Agent Discovery**: When agents register via the discovery protocol, their form
   schema (`AgentConfigSpecs`) is persisted alongside agent metadata, making configuration forms available to the UI
   without requiring the agent to be online.

3. **New CRUD API Endpoints**: Implement REST endpoints for agent configuration management:
    - `GET /agents/{agent_class}/{agent_id}/configuration` - Retrieve current configuration values
    - `PUT /agents/{agent_class}/{agent_id}/configuration` - Update configuration values
    - `GET /agents/classes` - List available agent classes for creating new instances
    - `POST /agents/` - Create new agent instance with custom configuration
    - `DELETE /agents/{agent_class}/{agent_id}` - Delete agent instance

4. **FormKit-Based Configuration UI**: The Admin UI renders dynamic configuration forms using FormKit, supporting
   complex nested structures through Group and Repeater elements, and dynamic model selection via API-driven dropdowns.

5. **Protected Default Configurations**: Default agent configurations (defined in agent code) cannot be deleted or
   overwritten, ensuring a fallback always exists.

## Consequences

### Positive Outcomes

- **Self-Service Configuration**: Administrators can customize agent behavior (prompts, RAG parameters, model selection)
  directly through the UI without developer involvement.
- **Dynamic Model Selection**: Form dropdowns can be populated from the LiteLLM model registry, ensuring users only see
  available models.
- **Type-Safe Validation**: FormKit validates user input against the schema before submission, preventing invalid
  configurations.

### Trade-offs and Considerations

- **Form Definition Required**: Agents must explicitly define FormKit form elements to expose configuration in the UI.
  This provides full control over form layout, labels, and validation but requires upfront effort from agent developers.
- **Schema Evolution**: When agent developers change `AgentConfig` fields, existing persisted configurations may need
  migration or may use stale schemas until agents re-register.
- **Discovery Dependency**: Form schemas are captured at agent discovery time; if an agent never comes online after
  deployment, its configuration form won't be available.
- **No Conditional Logic**: The current implementation generates static forms; conditional field visibility based on
  other field values is not yet supported.
