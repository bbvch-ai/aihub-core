from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.agents.visualizers.types.workflow_graph import WorkflowGraph
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.form.template_data import TemplateData
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class AgentClassDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after an agent discovery request, providing the form schema
    and validation specs needed to configure new agent instances.

    Contains:
    - Class-level metadata: name, description, icon (from the Agent class definition)
    - `form`: FormKit elements defining the configuration UI
    - `agent_config_specs`: Validation schema for form submissions
    - Event specifications for workflow integration

    Default values for form fields are defined within the FormKit elements themselves.
    """

    agent_class: Annotated[str, Field(description="The class name of the agent (e.g., 'RAGAgent').")]
    # Class-level metadata (describes the agent class itself, not instances)
    name: Annotated[LocaleString, Field(description="Display name for this agent class.")]
    description: Annotated[LocaleString, Field(description="Description of this agent class.")]
    icon: Annotated[str, Field(description="Icon for this agent class.")] = "mage:robot"
    is_conversational: Annotated[
        bool, Field(description="Whether the agent can participate in a chat-based conversation")
    ]
    is_schedulable: Annotated[
        bool, Field(description="Whether the agent can be run automatically on a cron schedule")
    ] = False
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(
            description="FormKit elements defining the agent configuration form. "
            "Default values are embedded in the elements themselves.",
        ),
    ]
    agent_config_specs: Annotated[
        ConfigSpecs,
        Field(
            description="Validation specification including the JSON schema for form submissions. "
            "Used by ModelCreationService to create Pydantic models for validation.",
        ),
    ]
    start_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a start event type and schema. "
            "This lets consumers understand exactly how to initiate the agent's workflow.",
        ),
    ]
    stop_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a stop event type and schema. "
            "This lets consumers understand exactly how to initiate the agent's workflow.",
        ),
    ]
    hitl_request_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a human-in-the-loop request event type "
            "and schema. These events allow the agent to request human intervention during its workflow."
        ),
    ]
    hitl_response_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` objects, each describing a human-in-the-loop response event type "
            "and schema. These events allow humans to respond to agent HITL requests."
        ),
    ]
    network_graph: Annotated[
        WorkflowGraph,
        Field(
            description="A network graph of the agent, showing how different components are connected and interact.",
        ),
    ]
    templates: Annotated[
        list[TemplateData],
        Field(description="List of profile templates for quick profile creation in the Admin UI."),
    ] = []
