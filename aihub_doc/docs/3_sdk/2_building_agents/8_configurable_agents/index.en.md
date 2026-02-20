---
title: Configurable Agent Forms
---

# Configurable Agent Forms

This guide explains how to define agent configuration forms that allow administrators to create and customize agent
profiles without code changes.

## Overview

The SDK uses the **Form Duality Pattern** where a single Pydantic model serves two purposes:

1. **Form Mode**: Fields contain `FormkitElement` instances that define the UI form
2. **Data Mode**: Fields contain primitive values that hold validated configuration

This pattern ensures the form schema and data model cannot become desynchronized.

## Basic Pattern

### Defining a Configurable AgentConfig

```python
from typing import Annotated
from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.constraints import Ge, Le
from aihub_lib.nats.events.form.elements import InputNumber, InputText


class MyAgentConfig(AgentConfig):
    # Field with duality: str for data mode, InputText for form mode
    model_name: Annotated[
        str | InputText,
        Field(description="The LLM model to use"),
    ] = "gpt-4"

    # Numeric field with constraints
    temperature: Annotated[
        float | InputNumber,
        Field(description="LLM temperature"),
        Ge(0.0),  # Minimum value
        Le(1.0),  # Maximum value
    ] = 0.7

    @classmethod
    def as_form(cls) -> "MyAgentConfig":
        """Create form-mode config with FormKit elements for UI rendering."""
        base = AgentConfig.as_form()
        return cls(
            # Inherit base fields from AgentConfig
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            # Define form elements for custom fields
            model_name=InputText(
                label=LocaleString(en="Model", de="Modell"),
                help=LocaleString(en="Select the LLM model to use"),
            ),
            temperature=InputNumber(
                label=LocaleString(en="Temperature", de="Temperatur"),
                help=LocaleString(en="Controls response creativity (0=focused, 1=creative)"),
                min=0.0,
                max=1.0,
                step=0.1,
            ),
        )
```

### Registering with AgentRunner

```python
from aihub_agent.runners.AgentRunner import AgentRunner

from .MyAgent import MyAgent
from .MyAgentConfig import MyAgentConfig


async def main():
    runner = AgentRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig.as_form(),  # Form mode!
    )
    await runner.run_forever()
```

The `as_form()` call creates a config instance in form mode. When the agent registers via discovery, the form schema is
extracted and stored. Administrators can then create profiles through the Admin UI.

## Available FormKit Elements

### Text Input

```python
from aihub_lib.nats.events.form.elements import InputText

system_prompt: Annotated[str | InputText, Field()] = "You are a helpful assistant."

# In as_form():
system_prompt=InputText(
    label=LocaleString(en="System Prompt"),
    help=LocaleString(en="Instructions for the agent"),
    required=True,
)
```

### Numeric Input

```python
from aihub_lib.nats.events.form.elements import InputNumber
from aihub_lib.nats.events.form.constraints import Ge, Le

max_tokens: Annotated[int | InputNumber, Field(), Ge(1), Le(4096)] = 1024

# In as_form():
max_tokens=InputNumber(
    label=LocaleString(en="Max Tokens"),
    min=1,
    max=4096,
    step=1,
)
```

### Boolean Toggle

```python
from aihub_lib.nats.events.form.elements import ToggleSwitch

enable_citations: Annotated[bool | ToggleSwitch, Field()] = True

# In as_form():
enable_citations=ToggleSwitch(
    label=LocaleString(en="Enable Citations"),
    help=LocaleString(en="Include source citations in responses"),
)
```

### Dropdown Selection

```python
from aihub_lib.nats.events.form.elements import Select

response_format: Annotated[str | Select, Field()] = "text"

# In as_form():
response_format=Select(
    label=LocaleString(en="Response Format"),
    options=[
        {"label": "Plain Text", "value": "text"},
        {"label": "Markdown", "value": "markdown"},
        {"label": "JSON", "value": "json"},
    ],
)
```

### Multi-Language Input

```python
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements import LocaleInput

greeting: Annotated[LocaleString | LocaleInput, Field()]

# In as_form():
greeting=LocaleInput(
    label=LocaleString(en="Greeting Message"),
    help=LocaleString(en="Shown when conversation starts"),
)
```

### Model Selector

```python
from aihub_lib.nats.events.form.elements import ModelSelect

llm_model: Annotated[str | ModelSelect, Field()] = "gpt-4"

# In as_form():
llm_model=ModelSelect(
    label=LocaleString(en="Language Model"),
    help=LocaleString(en="Select from available models"),
)
```

The `ModelSelect` element automatically populates from the LiteLLM model registry at runtime.

## Form-Safe Constraints

Standard Pydantic constraints (`Field(ge=0, le=1)`) don't work with the duality pattern because they can't validate
FormkitElement types. Use SDK-provided constraints instead:

```python
from aihub_lib.nats.events.form.constraints import Ge, Le, Gt, Lt, MinLen, MaxLen, Pattern

# Numeric constraints
temperature: Annotated[float | InputNumber, Ge(0.0), Le(1.0)] = 0.7
min_score: Annotated[float | InputNumber, Gt(0.0)] = 0.1  # Greater than (exclusive)

# String constraints
api_key: Annotated[str | InputText, MinLen(10), MaxLen(100)] = ""
agent_id: Annotated[str | InputText, Pattern(r"^[a-z0-9_-]+$")] = ""
```

These constraints skip validation when the field contains a FormkitElement, enabling Pydantic validation to work in both
modes.

## Non-Configurable Fields

Some fields should not appear in the form (deployment-specific configuration). Omit the FormKit element alternative:

```python
class MyAgentConfig(AgentConfig):
    # Configurable (appears in form) - has FormKit alternative
    model_name: Annotated[str | InputText, Field()] = "gpt-4"

    # Non-configurable (set at deployment) - no FormKit alternative
    channel_config: TeamsConfig

    @classmethod
    def as_form(cls, channel_config: TeamsConfig) -> "MyAgentConfig":
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            model_name=InputText(label=LocaleString(en="Model")),
            channel_config=channel_config,  # Actual value, not FormKit element
        )
```

Non-configurable fields are merged with user-submitted configuration at runtime. The form only shows configurable
fields.

## Nested Forms

Forms can contain other forms using the `Group` element:

```python
from aihub_lib.nats.events.form.Form import Form
from aihub_lib.nats.events.form.elements import InputNumber, ModelSelect


class LLMConfig(Form):
    """Nested form for LLM settings."""

    model_name: Annotated[str | ModelSelect, Field()] = "gpt-4"
    temperature: Annotated[float | InputNumber, Ge(0.0), Le(1.0)] = 0.7
    max_tokens: Annotated[int | InputNumber, Ge(1), Le(4096)] = 1024

    @classmethod
    def as_form(cls) -> "LLMConfig":
        return cls(
            model_name=ModelSelect(label=LocaleString(en="Model")),
            temperature=InputNumber(label=LocaleString(en="Temperature"), min=0.0, max=1.0),
            max_tokens=InputNumber(label=LocaleString(en="Max Tokens"), min=1, max=4096),
        )


class MyAgentConfig(AgentConfig):
    llm: Annotated[LLMConfig, Field(title="LLM Settings")]

    @classmethod
    def as_form(cls) -> "MyAgentConfig":
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            llm=LLMConfig.as_form(),  # Nested form
        )
```

Nested forms automatically render as collapsible `Group` elements in the UI.

## Repeater Forms (Arrays)

For lists of configurable items, use a list of forms:

```python
class ExampleForm(Form):
    """Single example for few-shot learning."""

    input_text: Annotated[str | InputText, Field()] = ""
    expected_output: Annotated[str | InputText, Field()] = ""

    @classmethod
    def as_form(cls) -> "ExampleForm":
        return cls(
            input_text=InputText(label=LocaleString(en="Input")),
            expected_output=InputText(label=LocaleString(en="Expected Output")),
        )


class MyAgentConfig(AgentConfig):
    examples: Annotated[list[ExampleForm], Field(title="Few-Shot Examples")]

    @classmethod
    def as_form(cls) -> "MyAgentConfig":
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            examples=[ExampleForm.as_form()],  # List with one template
        )
```

Lists of forms render as `Repeater` elements, allowing users to add/remove items dynamically.

## Accessing Configuration in Steps

The dispatcher injects the validated configuration into step methods via type annotation:

```python
from aihub_agent.workflow.decorators.step import step


class MyAgent(Agent):
    @step()
    async def process_message(
        self,
        event: UserMessageEvent,
        agent_config: MyAgentConfig,  # Injected by dispatcher
    ) -> ResponseEvent:
        # Access configuration values
        model = agent_config.model_name
        temperature = agent_config.temperature

        # Use nested config
        max_tokens = agent_config.llm.max_tokens

        # ...
```

Configuration is fetched via RPC when the agent receives a `StartEvent`, validated against the Pydantic model, and
cached for the duration of the run.

## Conditional Field Visibility

Show or hide fields based on other field values:

```python
use_custom_prompt: Annotated[bool | ToggleSwitch, Field()] = False
custom_prompt: Annotated[str | InputText, Field()] = ""

# In as_form():
use_custom_prompt=ToggleSwitch(label=LocaleString(en="Use Custom Prompt")),
custom_prompt=InputText(
    label=LocaleString(en="Custom Prompt"),
    condition_if="$get(use_custom_prompt).value === true",  # FormKit condition
)
```

The `condition_if` parameter uses FormKit's expression syntax. The field only appears when the condition evaluates to
true.

## Complete Example

```python
from typing import Annotated

from pydantic import Field

from aihub_agent.agents.Agent import Agent
from aihub_agent.runners.AgentRunner import AgentRunner
from aihub_agent.workflow.decorators.step import step
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.StopEvent import StopEvent
from aihub_lib.nats.events.control.UserMessageEvent import UserMessageEvent
from aihub_lib.nats.events.form.constraints import Ge, Le
from aihub_lib.nats.events.form.elements import InputNumber, InputText, ModelSelect, ToggleSwitch


class QAAgentConfig(AgentConfig):
    """Configuration for a question-answering agent."""

    model_name: Annotated[str | ModelSelect, Field(description="LLM model")] = "gpt-4"
    temperature: Annotated[float | InputNumber, Field(), Ge(0.0), Le(1.0)] = 0.3
    system_prompt: Annotated[str | InputText, Field()] = "You are a helpful assistant."
    enable_citations: Annotated[bool | ToggleSwitch, Field()] = True

    @classmethod
    def as_form(cls) -> "QAAgentConfig":
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            model_name=ModelSelect(
                label=LocaleString(en="Model", de="Modell"),
                help=LocaleString(en="Language model for generating responses"),
            ),
            temperature=InputNumber(
                label=LocaleString(en="Temperature", de="Temperatur"),
                help=LocaleString(en="Lower = more focused, Higher = more creative"),
                min=0.0,
                max=1.0,
                step=0.1,
            ),
            system_prompt=InputText(
                label=LocaleString(en="System Prompt", de="System-Prompt"),
                help=LocaleString(en="Instructions for the assistant"),
            ),
            enable_citations=ToggleSwitch(
                label=LocaleString(en="Enable Citations", de="Zitate aktivieren"),
                help=LocaleString(en="Include source references in answers"),
            ),
        )


class QAAgent(Agent):
    @step()
    async def answer_question(
        self,
        event: UserMessageEvent,
        agent_config: QAAgentConfig,
    ) -> StopEvent:
        # Use configuration
        model = agent_config.model_name
        temp = agent_config.temperature
        citations = agent_config.enable_citations

        # ... generate answer using config ...

        return StopEvent()


async def main():
    runner = AgentRunner(
        agent_type=QAAgent,
        agent_config=QAAgentConfig.as_form(),
    )
    await runner.run_forever()
```

## Best Practices

### Field Naming

- Use descriptive field names that make sense to administrators
- Provide `help` text explaining what each setting does
- Include reasonable default values

### Validation

- Always use constraints (`Ge`, `Le`, `Pattern`) for numeric and string fields
- Validate early to prevent invalid configurations from being saved

### Localization

- Use `LocaleString` for all user-facing text (labels, help, descriptions)
- Support at least German and English (`de`, `en`)

### Testing

- Test both form mode (`as_form()`) and data mode (with actual values)
- Verify form schema generation with `config.to_formkit_form()`
- Test configuration injection in step methods
