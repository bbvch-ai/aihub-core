from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.agents.agent import Agent
    from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent import ExpertAskingAgent
    from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
    from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
    from swiss_ai_hub.agent.agents.imap_agent.imap_agent import ImapAgent
    from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
    from swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent import NamespaceSelectionAgent
    from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
    from swiss_ai_hub.agent.agents.retrieval_agent.retrieval_agent import RetrievalAgent

__all__ = [
    "Agent",
    "ExpertAskingAgent",
    "ExpertRAGAgent",
    "FewShotAgent",
    "ImapAgent",
    "LLMWrappingAgent",
    "NamespaceSelectionAgent",
    "RAGAgent",
    "RetrievalAgent",
]

_LAZY_IMPORTS: dict[str, str] = {
    "Agent": "swiss_ai_hub.agent.agents.agent",
    "ExpertAskingAgent": "swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent",
    "ExpertRAGAgent": "swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent",
    "FewShotAgent": "swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent",
    "ImapAgent": "swiss_ai_hub.agent.agents.imap_agent.imap_agent",
    "LLMWrappingAgent": "swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent",
    "NamespaceSelectionAgent": "swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent",
    "RAGAgent": "swiss_ai_hub.agent.agents.rag_agent.rag_agent",
    "RetrievalAgent": "swiss_ai_hub.agent.agents.retrieval_agent.retrieval_agent",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
