from typing import Literal

from aihub_lib.generative_ai.retrievers import KnowledgeRetrievalOverride, RetrievalOverride
from aihub_lib.nats.events import AgentInTheLoop, RetrievalStartEvent

from aihub_agent.agents.configs import AgentReference, KnowledgeRetrievalAgentReference
from aihub_agent.agents.RagAgent.events.BucketNamespaceSelection import BucketNamespaceSelection


def _resolve_override_for_agent(
    agent_ref: AgentReference,
    bucket_namespace_selections: list[BucketNamespaceSelection] | None,
) -> RetrievalOverride | None:
    """Resolves the override for a specific agent based on bucket namespace selections.

    For KnowledgeRetrievalAgentReference, looks up the matching bucket and returns
    a KnowledgeRetrievalOverride with the selected namespaces.
    """
    if bucket_namespace_selections and isinstance(agent_ref, KnowledgeRetrievalAgentReference):
        for selection in bucket_namespace_selections:
            if selection.bucket_name == agent_ref.bucket_name:
                return KnowledgeRetrievalOverride(type="knowledge", namespaces=selection.namespaces)

    return None


def execute_invoke_retrieval(
    query: str,
    locale: Literal["de", "en", "fr", "it"],
    retrieval_agents: list[AgentReference],
    bucket_namespace_selections: list[BucketNamespaceSelection] | None = None,
) -> list[AgentInTheLoop.request]:
    """
    Builds AgentInTheLoop requests for invoking retrieval agents.
    """
    requests = []
    for agent_ref in retrieval_agents:
        override = _resolve_override_for_agent(agent_ref, bucket_namespace_selections)

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
