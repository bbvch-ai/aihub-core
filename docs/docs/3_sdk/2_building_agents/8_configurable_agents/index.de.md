---
title: Konfigurierbare Agentenformulare
source_sha: "dea97b0c7cdd335029ac01267a55446be0916c7917b4a9f4203f1d243a988883"
---

# Konfigurierbare Agentenformulare

Dieser Leitfaden erklärt, wie Sie Agenten-Konfigurationsformulare definieren, die es Administratoren ermöglichen, Agentenprofile ohne Codeänderungen zu erstellen und anzupassen.

## Überblick

Das SDK verwendet das **Formular-Dualitätsmuster**, bei dem ein einziges Pydantic-Modell zwei Zwecken dient:

1.  **Formularmodus**: Felder enthalten `FormkitElement`-Instanzen, die das UI-Formular definieren
2.  **Datenmodus**: Felder enthalten primitive Werte, die die validierte Konfiguration speichern

Dieses Muster stellt sicher, dass das Formularschema und das Datenmodell nicht desynchronisiert werden können.

## Grundlegendes Muster

### Definieren einer konfigurierbaren AgentConfig

```python
from typing import Annotated
from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.elements import InputNumber, InputText


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

### Registrierung beim AgentRunner

```python
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner

from .MyAgent import MyAgent
from .MyAgentConfig import MyAgentConfig


async def main():
    runner = AgentRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig.as_form(),  # Form mode!
    )
    await runner.run_forever()
```

Der Aufruf von `as_form()` erstellt eine Konfigurationsinstanz im Formularmodus. Wenn der Agent sich über Discovery registriert, wird das Formularschema extrahiert und gespeichert. Administratoren können dann Profile über die Admin-Benutzeroberfläche erstellen.

## Verfügbare FormKit-Elemente

### Texteingabe

```python
from swiss_ai_hub.core.form.elements import InputText

system_prompt: Annotated[str | InputText, Field()] = "You are a helpful assistant."

# In as_form():
system_prompt=InputText(
    label=LocaleString(en="System Prompt"),
    help=LocaleString(en="Instructions for the agent"),
    required=True,
)
```

### Numerische Eingabe

```python
from swiss_ai_hub.core.form.elements import InputNumber
from swiss_ai_hub.core.form.constraints import Ge, Le

max_tokens: Annotated[int | InputNumber, Field(), Ge(1), Le(4096)] = 1024

# In as_form():
max_tokens=InputNumber(
    label=LocaleString(en="Max Tokens"),
    min=1,
    max=4096,
    step=1,
)
```

### Boolescher Umschalter

```python
from swiss_ai_hub.core.form.elements import ToggleSwitch

enable_citations: Annotated[bool | ToggleSwitch, Field()] = True

# In as_form():
enable_citations=ToggleSwitch(
    label=LocaleString(en="Enable Citations"),
    help=LocaleString(en="Include source citations in responses"),
)
```

### Dropdown-Auswahl

```python
from swiss_ai_hub.core.form.elements import Select

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

### Mehrsprachige Eingabe

```python
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.form.elements import LocaleInput

greeting: Annotated[LocaleString | LocaleInput, Field()]

# In as_form():
greeting=LocaleInput(
    label=LocaleString(en="Greeting Message"),
    help=LocaleString(en="Shown when conversation starts"),
)
```

### Modell-Auswahl

```python
from swiss_ai_hub.core.form.elements import ModelSelect

llm_model: Annotated[str | ModelSelect, Field()] = "gpt-4"

# In as_form():
llm_model=ModelSelect(
    label=LocaleString(en="Language Model"),
    help=LocaleString(en="Select from available models"),
)
```

Das `ModelSelect`-Element wird zur Laufzeit automatisch aus dem LiteLLM-Modellregister befüllt.

## Formularsichere Constraints

Standard-Pydantic-Constraints (`Field(ge=0, le=1)`) funktionieren nicht mit dem Dualitätsmuster, da sie `FormkitElement`-Typen nicht validieren können. Verwenden Sie stattdessen die vom SDK bereitgestellten Constraints:

```python
from swiss_ai_hub.core.form.constraints import Ge, Le, Gt, Lt, MinLen, MaxLen, Pattern

# Numeric constraints
temperature: Annotated[float | InputNumber, Ge(0.0), Le(1.0)] = 0.7
min_score: Annotated[float | InputNumber, Gt(0.0)] = 0.1  # Greater than (exclusive)

# String constraints
api_key: Annotated[str | InputText, MinLen(10), MaxLen(100)] = ""
agent_id: Annotated[str | InputText, Pattern(r"^[a-z0-9_-]+$")] = ""
```

Diese Constraints überspringen die Validierung, wenn das Feld ein `FormkitElement` enthält, wodurch die Pydantic-Validierung in beiden Modi funktioniert.

## Nicht-konfigurierbare Felder

Einige Felder sollten nicht im Formular erscheinen (bereitstellungsspezifische Konfiguration). Lassen Sie die FormKit-Element-Alternative weg:

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

Nicht-konfigurierbare Felder werden zur Laufzeit mit der vom Benutzer übermittelten Konfiguration zusammengeführt. Das Formular zeigt nur konfigurierbare Felder an.

## Verschachtelte Formulare

Formulare können andere Formulare unter Verwendung des `Group`-Elements enthalten:

```python
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.form.elements import InputNumber, ModelSelect


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

Verschachtelte Formulare werden in der Benutzeroberfläche automatisch als einklappbare `Group`-Elemente gerendert.

## Repeater-Formulare (Arrays)

Für Listen von konfigurierbaren Elementen verwenden Sie eine Liste von Formularen:

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

Listen von Formularen werden als `Repeater`-Elemente gerendert, die es Benutzern ermöglichen, Elemente dynamisch hinzuzufügen/zu entfernen.

## Zugriff auf Konfiguration in Schritten

Der Dispatcher injiziert die validierte Konfiguration über Typannotationen in Schrittmethoden:

```python
from swiss_ai_hub.agent.workflow.decorators.step import step


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

Die Konfiguration wird über RPC abgerufen, wenn der Agent ein `StartEvent` erhält, gegen das Pydantic-Modell validiert und für die Dauer des Laufs zwischengespeichert.

## Bedingte Feldsichtbarkeit

Felder basierend auf den Werten anderer Felder anzeigen oder verbergen:

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

Der Parameter `condition_if` verwendet die Ausdruckssyntax von FormKit. Das Feld wird nur angezeigt, wenn die Bedingung als wahr ausgewertet wird.

## Vollständiges Beispiel

```python
from typing import Annotated

from pydantic import Field

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.events.control.stop_event import StopEvent
from swiss_ai_hub.core.events.control.user_message_event import UserMessageEvent
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.elements import InputNumber, InputText, ModelSelect, ToggleSwitch


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

### Feld-Benennung

- Verwenden Sie beschreibende Feldnamen, die für Administratoren verständlich sind
- Stellen Sie `help`-Text bereit, der erklärt, was jede Einstellung bewirkt
- Fügen Sie sinnvolle Standardwerte hinzu

### Validierung

- Verwenden Sie immer Constraints (`Ge`, `Le`, `Pattern`) für numerische Felder und String-Felder
- Validieren Sie frühzeitig, um zu verhindern, dass ungültige Konfigurationen gespeichert werden

### Lokalisierung

- Verwenden Sie `LocaleString` für alle benutzerspezifischen Texte (Labels, Hilfe, Beschreibungen)
- Unterstützen Sie mindestens Deutsch und Englisch (`de`, `en`)

### Testen

- Testen Sie sowohl den Formularmodus (`as_form()`) als auch den Datenmodus (mit tatsächlichen Werten)
- Überprüfen Sie die Generierung des Formularschemas mit `config.to_formkit_form()`
- Testen Sie die Konfigurationsinjektion in Schrittmethoden
