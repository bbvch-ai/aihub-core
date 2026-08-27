from typing import Annotated

from pydantic import BaseModel, Field


class AgentRef(BaseModel):
    """
    Reference to a specific agent instance.

    Used as the data type when AgentSelector is in data mode.
    Similar to MilvusVectorStoreConfig for VectorStoreInput.

    This model is validated directly from AgentSelector form submissions.
    The AgentSelector component emits {"agent_class": str, "agent_id": str}.

    ### Example Usage

    ```python
    from swiss_ai_hub.core.agents.agent_ref import AgentRef
    from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector

    class MyConfig(Form):
        target_agent: Annotated[
            AgentRef | AgentSelector,
            Field(description="The target agent to invoke"),
        ]

        @classmethod
        def as_form(cls) -> "MyConfig":
            return cls(
                target_agent=AgentSelector(
                    label=LocaleString(en="Target Agent"),
                ),
            )

    # Data mode - from submission:
    config = MyConfig(
        target_agent=AgentRef(
            agent_class="my_agent_class",
            agent_id="my_agent_id",
        ),
    )

    # Access in code:
    agent_class = config.target_agent.agent_class
    agent_id = config.target_agent.agent_id
    ```
    """

    # Both halves must be non-empty: `PartialAgentTopic.to_subject` renders a blank segment as the NATS
    # wildcard `*`, so an empty id publishes the delegation to a subject no instance is subscribed to and
    # the caller waits for a reply that never arrives.
    agent_class: Annotated[str, Field(description="The agent class name", min_length=1)]
    agent_id: Annotated[str, Field(description="The agent instance ID", min_length=1)]
