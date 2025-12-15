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
    """Builds AgentInTheLoop requests for invoking retrieval agents."""
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
