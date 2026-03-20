# Enable Dynamic Agent Configuration Through Admin UI

## Context

The Swiss AI Hub platform supports multiple agent types (RAG agents, specialized assistants, etc.) that each have
runtime configuration requirements. Previously, modifying agent behavior required:

- **Code Changes**: Developers had to modify `AgentConfig` classes and redeploy services to change configuration values.
- **Technical Barrier**: Non-technical users (administrators, business analysts) could not customize agent behavior to
  meet specific use cases without developer involvement.

While agents already had a configuration system through Pydantic-based `AgentConfig` classes, there was no way to expose
these configurations to end users through the UI or to persist user-customized configurations separately from the
default values.

### Agent Blueprint vs Agent Profile

The platform now distinguishes between two concepts:

- **Agent Blueprint** (Agent Class): The code-level definition containing workflow steps, form schema, event
  specifications, and default configuration. Discovered automatically when agents come online and stored in the
  `agent_classes` collection.
- **Agent Profile** (Agent Instance): A user-created configuration of a blueprint. Has a unique ID, name, description,
  icon, and specific settings. Multiple profiles can be created from one blueprint. Stored in the `agent_configs`
  collection.

This separation enables self-service deployment: developers define blueprints, while administrators create and configure
profiles through the UI without code changes.

## Decision Drivers

- **User Self-Service**: Enable administrators and business users to customize agent configurations without code changes
  or developer involvement.
- **Type Safety Preservation**: Configuration changes should still be validated against the agent's expected schema,
  preventing invalid configurations.
- **Single Source of Truth**: Form schema and data model should be defined once to avoid desynchronization.
- **Developer Experience**: Minimal boilerplate for exposing configuration through the UI.

## Decision

We will implement dynamic agent configuration through the Admin UI using the **Form Duality Pattern**:

### 1. Form Duality Pattern

A single Pydantic model serves two purposes through type unions:

- **Form Mode**: Fields contain `FormkitElement` instances (e.g., `InputText`, `InputNumber`, `Select`) for UI rendering
- **Data Mode**: Fields contain primitive values (e.g., `str`, `float`, `bool`) for validated configuration

```python
class MyAgentConfig(AgentConfig):
    # Form duality: float for data mode, InputNumber for form mode
    temperature: Annotated[float | InputNumber, Field(description="LLM temperature"), Ge(0.0), Le(1.0)] = 0.7

    @classmethod
    def as_form(cls) -> "MyAgentConfig":
        """Create form-mode config with FormKit elements for UI rendering."""
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            temperature=InputNumber(label=LocaleString(en="Temperature"), min=0.0, max=1.0),
        )
```

### 2. FormKit Element Aliases

FormKit elements use Pydantic aliases to handle MongoDB's `$` prefix restriction:

- `formkit` stored in DB → `$formkit` in JSON response
- `condition_if` stored in DB → `if` in JSON response (for conditional visibility)
- `ref` stored in DB → `id` in JSON response

This enables storing form schemas in MongoDB while generating valid FormKit schemas for the frontend.

### 3. Non-Configurable vs Configurable Fields

Fields can be marked as non-configurable (deployment-specific) by omitting the FormKit element alternative in the type
union:

```python
class MyAgentConfig(AgentConfig):
    # Configurable (appears in form) - has FormKit alternative
    model_name: str | InputText = "gpt-4"

    # Non-configurable (set at deployment) - no FormKit alternative
    channel_config: TeamsConfig
```

Non-configurable values are merged with user-submitted configuration at runtime.

### 4. Form-Safe Constraints

Custom constraint validators (`Ge`, `Le`, `Pattern`, `MinLen`, `MaxLen`) that skip validation when the field contains a
FormkitElement, enabling Pydantic validation to work with the duality pattern.

### 5. Agent Discovery and Registration

When agents register via `AgentRunner`, the form-mode config is used:

```python
runner = AgentRunner(
    agent_type=MyAgent,
    agent_config=MyAgentConfig.as_form(),  # Form mode for discovery
)
```

The discovery response includes:

- Form schema (extracted via `to_formkit_form()`)
- JSON schema for validation (via `AgentConfigSpecs.from_model()`)
- Start/stop event specifications
- Workflow network graph

### 6. Configuration Injection

At runtime, the `AgentDispatcher` fetches the configuration for the specific agent profile via RPC, merges it with
non-configurable defaults, validates it against the Pydantic model, and injects it into step methods via type
annotation:

```python
@step()
async def my_step(self, event: MyEvent, agent_config: MyAgentConfig):
    model = agent_config.model_name  # Validated configuration value
```

### 7. Two-Collection Persistence

- **`agent_classes`** (`AgentClassEntity`): One document per agent type, updated by discovery. Contains form schema,
  event specs, workflow graph, online status.
- **`agent_configs`** (`AgentConfigEntityDocument`): Many documents per agent type. Contains instance-specific
  configuration values, name, description, icon.

### 8. REST API Endpoints

Agent Classes (blueprints):

- `GET /agents/classes` - List all agent classes
- `GET /agents/classes/{agent_class}` - Get specific class with form schema

Agent Instances (profiles):

- `GET /agents/classes/{agent_class}/instances` - List instances of a class
- `POST /agents/classes/{agent_class}/instances` - Create new instance
- `GET /agents/classes/{agent_class}/instances/{agent_id}` - Get instance
- `PUT /agents/classes/{agent_class}/instances/{agent_id}` - Update instance configuration
- `DELETE /agents/classes/{agent_class}/instances/{agent_id}` - Delete instance

Cross-class:

- `GET /agents/instances` - List all instances across all classes

## Consequences

### Positive Outcomes

- **Self-Service Configuration**: Administrators can create and customize agent profiles (prompts, RAG parameters, model
  selection) directly through the UI without developer involvement.
- **Single Source of Truth**: Form schema and data model are defined in one place, preventing desynchronization.
- **Type-Safe End-to-End**: Pydantic validates both form submission and runtime configuration access.
- **Conditional Field Visibility**: FormKit's `condition_if` (aliased from `if`) enables dynamic form sections based on
  other field values.
- **Multi-Language Support**: `LocaleInput` element enables multi-language names and descriptions.
- **Nested Configuration**: Forms can contain nested `Group` elements and `Repeater` arrays for complex configuration
  structures.
- **Dynamic Model Selection**: `ModelSelect` element populates from the LiteLLM model registry at runtime.

### Trade-offs and Considerations

- **Form Definition Required**: Agents must implement `as_form()` class method and use type unions to expose
  configuration in the UI. This provides full control but requires understanding the duality pattern.
- **Schema Evolution**: When agent developers change `AgentConfig` fields, existing persisted configurations may use
  stale schemas until agents re-register.
- **Discovery Dependency**: Form schemas are captured at agent discovery time; if an agent never comes online after
  deployment, its configuration form won't be available.
- **Constraint Validators**: Standard Pydantic constraints (`ge=`, `le=`) don't work with duality pattern; developers
  must use SDK-provided constraints (`Ge()`, `Le()`).
