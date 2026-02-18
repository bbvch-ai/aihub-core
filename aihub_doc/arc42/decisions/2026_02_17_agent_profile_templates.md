# Agent Profile Templates for Quick Profile Creation

## Context

The AI-Hub platform separates agent blueprints (code-level definitions discovered at runtime) from agent profiles
(admin-created configurations stored in the DB). This separation was introduced in the
[Dynamic Agent Configuration ADR](2026_01_07_enable_dynamic_agent_configuration_ui.md) to enable self-service
deployment: developers define blueprints, administrators create profiles through the UI.

After #887 removed the legacy default config mechanism, new agents required manual profile creation from scratch before
they could be used. This conflicted with the platform's "batteries included" philosophy — a freshly deployed agent
should be easy to get running without deep knowledge of its configuration options.

An initial implementation (commit 884c803) introduced a single `default_profile` parameter on `AgentRunner` /
`ProcessRunner` that auto-created a profile in the database during discovery. While functional, this approach had
drawbacks identified during team review.

## Decision Drivers

- **Batteries included**: New agents should be easy to set up without reading documentation or understanding every
  configuration field.
- **Explicit over implicit**: Profiles that exist in the system should be consciously created by an administrator, not
  silently materialized by infrastructure code.
- **Multiple starting points**: Some agents have several valid configurations (e.g., a RAG agent optimized for Q&A vs.
  summarization). A single default cannot represent this.
- **No orphaned state**: Auto-creation during discovery can produce profiles that nobody expects or uses, especially in
  multi-agent deployments.
- **Minimal friction**: Creating a profile from a template should take no more than 2 clicks (select template → save).

## Decision

We replace the auto-created default profile with **profile templates** — a list of predefined configurations declared in
Python and transmitted during agent/process discovery.

### 1. Template Declaration

Agent and process runners accept an optional list of templates alongside the form-mode config:

```python
runner = AgentRunner(
    agent_type=MyAgent,
    agent_config=MyAgentConfig.as_form(),
    templates=[
        MyAgentConfig(
            agent_id="qa-mode",
            name=LocaleString(en="Q&A Mode", de="Q&A-Modus"),
            description=LocaleString(en="Optimized for question answering"),
            temperature=0.3,
            max_chunks=10,
        ),
        MyAgentConfig(
            agent_id="summary-mode",
            name=LocaleString(en="Summarization Mode", de="Zusammenfassungsmodus"),
            description=LocaleString(en="Optimized for document summarization"),
            temperature=0.7,
            max_chunks=5,
        ),
    ],
)
```

Templates are data-mode `AgentConfig` / `ProcessConfig` instances. They use the same `to_template_data()` method
(filtering to configurable + identity fields) to produce the payload sent during discovery.

### 2. Discovery Transport

The `AgentClassDiscoveryResponseEvent` and `ProcessClassDiscoveryResponseEvent` carry a `templates` field (list of
dicts) instead of a single `default_profile`. The API persists these templates alongside the agent/process class
metadata.

### 3. Admin UI Workflow

When an admin creates a new profile:

1. The UI shows a "Select template" step if templates exist for the agent class.
2. Selecting a template prefills all form fields with the template values.
3. The admin can review, adjust, and save — or skip templates and start from scratch.

### 4. No Auto-Creation

Templates never create profiles automatically. A profile only exists after explicit admin action. This means a freshly
deployed agent with templates has no active profiles until an admin creates one.

## Consequences

### Positive

- Administrators maintain full control over which profiles exist in their environment.
- Multiple templates per agent cover different use cases without forcing a single "default".
- Template selection + save is fast (2 clicks), preserving the low-friction goal.
- Templates are defined in Python alongside the agent code, keeping configuration close to the source.
- No database writes during discovery — discovery remains a read/broadcast operation.

### Trade-offs

- Agents do not work out-of-the-box after first deployment — an admin must create at least one profile. This is an
  intentional trade-off: explicitness over convenience.
- Template definitions add a small amount of boilerplate to agent runner setup. This is comparable to the existing
  `as_form()` pattern and follows the same conventions.
- The API must store and serve template data per agent class, adding a field to the `agent_classes` / `process_classes`
  collections.
