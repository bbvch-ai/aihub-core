"""Extracted function for invoking retrieval agents."""

from typing import Literal

from aihub_lib.generative_ai.retrievers import RetrievalOverride
from aihub_lib.nats.events import AgentInTheLoop, RetrievalStartEvent

from aihub_agent.agents.RagAgent.configs.AgentReference import AgentReference


def execute_invoke_retrieval(
    query: str,
    locale: Literal["de", "en", "fr", "it"],
    retrieval_agents: list[AgentReference],
    retrieval_overrides: dict[str, RetrievalOverride] | None = None,
) -> list[AgentInTheLoop.request]:
    """
    Builds AgentInTheLoop requests for invoking retrieval agents.

    Args:
        query: The search query to send to retrieval agents.
        locale: The locale for the retrieval.
        retrieval_agents: List of retrieval agent references to invoke.
        retrieval_overrides: Optional dict mapping agent_id to type-specific overrides.

    Returns:
        List of AgentInTheLoop.request objects ready to be returned from a step.
    """
    requests = []
    for agent_ref in retrieval_agents:
        override = retrieval_overrides.get(agent_ref.agent_id) if retrieval_overrides else None

        requests.append(
            AgentInTheLoop.invoke(
                agent_class=agent_ref.agent_class,
                agent_id=agent_ref.agent_id,
                start_event=RetrievalStartEvent(
                    question=query,
                    locale=locale,
                    override=override,
                ),
            )
        )

    return requests
