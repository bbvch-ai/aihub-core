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

    # Both halves must be a single NATS-safe token. Two consumers already require exactly that, and each
    # fails worse than a validation error when it is not met:
    #   - `PartialAgentTopic.to_subject` renders a blank segment as the wildcard `*` and passes a space, a
    #     `.` or a `>` straight through, so a malformed half publishes the delegation to a subject no
    #     instance is subscribed to and the caller waits for a reply that never arrives.
    #   - `AccessChecker.validate_permission_template` *raises* `ValueError` — a 500, not a 403 — on any
    #     segment outside `[a-z0-9_-]` case-insensitively, which is the class below. Both halves reach it
    #     through `AgentSelector.validate_authorization`.
    # Nothing that ever worked is rejected: an `agent_class` is always a Python class name, and every real
    # `agent_id` already satisfies `AgentConfig.agent_id`'s `^[a-z0-9_-]+$`.
    #
    # Anchored deliberately: pydantic-core treats `pattern` as a *search*, so an unanchored `\S` accepted
    # `"  RAGAgent  "`. `min_length=1` is redundant against `+` but kept for its message — a blank half is
    # the failure admins hit, and "at least 1 character" says more than a regex.
    #
    # This is a field shape, not the cross-field invariant ADR
    # `2026_08_07_agent_config_failures_surface_as_exception_events` moves out of `model_validate`. That
    # decision turns on JSON Schema being unable to carry a cross-field validator: the API cannot apply it
    # at save time, the bad config is stored, and `model_validate` on the dispatch hot path becomes the only
    # enforcement point — an outage, not a validation error. `min_length` and `pattern` invert that premise;
    # they survive into the schema jambo rebuilds the save-path model from, which is also why `pattern`
    # rather than `strip_whitespace`.
    agent_class: Annotated[str, Field(description="The agent class name", min_length=1, pattern=r"^[A-Za-z0-9_-]+$")]
    agent_id: Annotated[str, Field(description="The agent instance ID", min_length=1, pattern=r"^[A-Za-z0-9_-]+$")]
