from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.BaseEvent import BaseEvent
from swiss_ai_hub.core.events.process.discovery.agent_in.AgentInSpecs import AgentInSpecs
from swiss_ai_hub.core.events.process.discovery.human_in.HumanInSpecs import HumanInSpecs
from swiss_ai_hub.core.events.process.discovery.ProcessConfigSpecs import ProcessConfigSpecs
from swiss_ai_hub.core.events.process.discovery.program_in.ProgramInSpecs import ProgramInSpecs
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.TemplateData import TemplateData
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class ProcessClassDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after a process discovery request, providing the form schema
    and validation specs needed to configure new process instances.

    Contains:
    - Class-level metadata: name, description, icon (from the Process class definition)
    - `form`: FormKit elements defining the configuration UI
    - `process_config_specs`: Validation schema for form submissions
    - Entity specifications (human, program, agent inputs)

    Default values for form fields are defined within the FormKit elements themselves.
    """

    process_class: Annotated[str, Field(description="The class name of the process (e.g., 'OnboardingProcess').")]
    # Class-level metadata (describes the process class itself, not instances)
    name: Annotated[LocaleString, Field(description="Display name for this process class.")]
    description: Annotated[LocaleString, Field(description="Description of this process class.")]
    icon: Annotated[str, Field(description="Icon for this process class.")] = "mage:broadcast"
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(
            description="FormKit elements defining the process configuration form. "
            "Default values are embedded in the elements themselves.",
        ),
    ]
    process_config_specs: Annotated[
        ProcessConfigSpecs,
        Field(
            description="Validation specification including the JSON schema for form submissions. "
            "Used to create Pydantic models for validation.",
        ),
    ]
    human_inputs: Annotated[
        list[HumanInSpecs], Field(description="List of human work events that the process can receive.")
    ]
    program_inputs: Annotated[
        list[ProgramInSpecs], Field(description="List of program work events that the process can receive.")
    ]
    agent_inputs: Annotated[
        list[AgentInSpecs], Field(description="List of agent work events that the process can receive.")
    ]
    templates: Annotated[
        list[TemplateData],
        Field(description="List of profile templates for quick profile creation in the Admin UI."),
    ] = []
