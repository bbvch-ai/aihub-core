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
    from swiss_ai_hub.core.agents.AgentRef import AgentRef
    from swiss_ai_hub.core.nats.events.form.elements.AgentSelector import AgentSelector

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

    agent_class: Annotated[str, Field(description="The agent class name")]
    agent_id: Annotated[str, Field(description="The agent instance ID")]
