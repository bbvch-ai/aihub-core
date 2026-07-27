from typing import Annotated, Any, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class AgentSelector(PrimeVueElement):
    """
    A FormKit element for selecting an agent class and instance ID.

    This element renders as a cascading selection:
    1. Agent class dropdown (loads from /api/v1/agents/classes)
    2. Agent ID dropdown (populated based on selected class from /api/v1/agents/classes/{class}/instances)

    The output is a structured object containing both the class name and the instance ID:
    {"agent_class": str, "agent_id": str}

    ### Optional Filtering by Start Event

    When `start_event` is specified, only agent classes that accept the given event type
    are shown. For example, `start_event="AskExpertStartEvent"` filters to only show agents
    whose `start_events` contain an event with matching `event_name` or `event_parents`.

    This is similar to ModelSelect's `mode` parameter for filtering by model type.

    ### Form Duality

    When used with AgentRef, the form submission is validated directly into AgentRef:

    ```python
    from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector
    from swiss_ai_hub.core.form.forms.AgentRef import AgentRef

    class MyConfig(Form):
        target_agent: Annotated[
            AgentRef | AgentSelector,
            Field(description="The target agent to invoke"),
        ]

        @classmethod
        def as_form(cls) -> "MyConfig":
            return cls(
                target_agent=AgentSelector(
                    label=LocaleString(en="Target Agent", de="Ziel-Agent"),
                    start_event="SomeStartEvent",  # Optional filter
                ),
            )

        # Data mode - from submission:
        config = MyConfig(
            target_agent=AgentRef(
                agent_class="my_agent_class",
                agent_id="my_agent_id",
            ),
        )
    ```
    """

    formkit: Annotated[
        Literal["agentSelector"],
        Field(description="Agent selector element."),
    ] = "agentSelector"

    start_event: Annotated[
        str | None,
        Field(
            description="Optional filter: only show agent classes that accept this start event type. "
            "Matches against event_name or event_parents in the agent's start_events.",
            alias="startEvent",
        ),
    ] = None

    class_placeholder: Annotated[
        LocaleString | str | None,
        Field(description="Placeholder for agent class select", alias="classPlaceholder"),
    ] = None

    id_placeholder: Annotated[
        LocaleString | str | None,
        Field(description="Placeholder for agent ID select", alias="idPlaceholder"),
    ] = None

    filter: Annotated[bool, Field(description="Whether to enable filtering/search")] = True

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.class_placeholder, LocaleString):
            self_copy.class_placeholder = t.extract(self_copy.class_placeholder)
        if isinstance(self_copy.id_placeholder, LocaleString):
            self_copy.id_placeholder = t.extract(self_copy.id_placeholder)
        return self_copy

    def validate_authorization(
        self,
        field_path: str,
        value: Any,
        access_checker: AccessChecker,
        accessible_tenant_ids: set[str],
        t: LocaleHandler,
    ) -> list[ConfigAuthorizationViolation]:
        if not isinstance(value, dict):
            return []

        agent_class = value.get("agent_class")
        agent_id = value.get("agent_id")
        if not agent_class or not agent_id:
            return []

        agent_ref = f"{agent_class}/{agent_id}"
        if not access_checker.has_access_to_agent(agent_class, agent_id):
            return [
                ConfigAuthorizationViolation(
                    field=field_path,
                    resource_type="agent",
                    resource=agent_ref,
                    message=t("lib.common.authorization.no_access_agent", agent=agent_ref),
                )
            ]
        return []
