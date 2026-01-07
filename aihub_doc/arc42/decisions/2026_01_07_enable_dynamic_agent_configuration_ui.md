# Enable Dynamic Agent Configuration Through Admin UI

## Context

The AI-Hub platform supports multiple agent types (RAG agents, specialized assistants, etc.) that each have runtime
configuration requirements. Previously, modifying agent behavior required:

- **Code Changes**: Developers had to modify `AgentConfig` classes and redeploy services to change configuration values.
- **Technical Barrier**: Non-technical users (administrators, business analysts) could not customize agent behavior to
  meet specific use cases without developer involvement.
- **Inconsistent Experience**: The process service already supported dynamic form-based configuration through the Admin
  UI, but agents lacked this capability, creating an inconsistent user experience across the platform.

While agents already had a configuration system through Pydantic-based `AgentConfig` classes, there was no way to expose
these configurations to end users through the UI or to persist user-customized configurations separately from the
default values.

## Decision Drivers

- **User Self-Service**: Enable administrators and business users to customize agent configurations without code changes
  or developer involvement.
- **Consistency with Process Service**: The process service already uses FormKit-based dynamic forms for configuration;
  agents should follow the same pattern.
- **Type Safety Preservation**: Configuration changes should still be validated against the agent's expected schema,
  preventing invalid configurations.
- **Minimal Developer Overhead**: Agent developers should not need to manually define UI forms; form generation should
  be automatic from existing Pydantic models.
- **Separation of Concerns**: Default configurations (defined in code) should remain separate from user customizations
  (stored in database).

## Decision

We will implement dynamic agent configuration through the Admin UI using the following approach:

1. **Extend AgentConfig to Generate FormKit Schemas**: The `AgentConfig` base class now inherits from `Form`, enabling
   automatic conversion of Pydantic field definitions to FormKit form elements via `to_formkit_form()`.

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
   complex nested structures through Group and Repeater elements.

5. **Protected Default Configurations**: Default agent configurations (defined in agent code) cannot be deleted or
   overwritten, ensuring a fallback always exists.

## Consequences

### Positive Outcomes

- **Self-Service Configuration**: Administrators can customize agent behavior (prompts, RAG parameters, model selection)
  directly through the UI without developer involvement.
- **Consistent User Experience**: Agent configuration now follows the same pattern as process configuration, providing a
  unified experience across the platform.
- **Automatic Form Generation**: Developers define configuration in Pydantic; forms are generated automatically without
  additional work.
- **Type-Safe Validation**: FormKit validates user input against the schema before submission, preventing invalid
  configurations.
- **Audit Trail**: Configuration changes are persisted in MongoDB, enabling tracking of who changed what.

### Trade-offs and Considerations

- **Form Complexity Limits**: Very complex nested configurations may require custom FormKit elements beyond the standard
  Group/Repeater components.
- **Schema Evolution**: When agent developers change `AgentConfig` fields, existing persisted configurations may need
  migration or may use stale schemas until agents re-register.
- **Discovery Dependency**: Form schemas are captured at agent discovery time; if an agent never comes online after
  deployment, its configuration form won't be available.
- **No Conditional Logic**: The current implementation generates static forms; conditional field visibility based on
  other field values is not yet supported.
