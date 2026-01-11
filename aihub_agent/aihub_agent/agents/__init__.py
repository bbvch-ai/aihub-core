"""Swiss AI-Hub agents package."""

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.AgentDeveloperAgent import AgentDeveloperAgent, AgentDeveloperAgentConfig
from aihub_agent.agents.ExpertAskingAgent import ExpertAskingAgent, ExpertAskingAgentConfig
from aihub_agent.agents.ExpertRagAgent import ExpertRAGAgent, ExpertRAGAgentConfig
from aihub_agent.agents.FewShotAgent import FewShotAgent, FewShotAgentConfig
from aihub_agent.agents.LLMWrappingAgent import LLMWrappingAgent, LLMWrappingAgentConfig
from aihub_agent.agents.NamespaceSelectionAgent import NamespaceSelectionAgent, NamespaceSelectionAgentConfig
from aihub_agent.agents.RagAgent import RAGAgent, RAGAgentConfig
from aihub_agent.agents.RetrievalAgent import RetrievalAgent, RetrievalAgentConfig
from aihub_agent.agents.WebuiAgent import WebuiAgent, WebuiAgentConfig

__all__ = [
    "Agent",
    "AgentDeveloperAgent",
    "AgentDeveloperAgentConfig",
    "ExpertAskingAgent",
    "ExpertAskingAgentConfig",
    "ExpertRAGAgent",
    "ExpertRAGAgentConfig",
    "FewShotAgent",
    "FewShotAgentConfig",
    "LLMWrappingAgent",
    "LLMWrappingAgentConfig",
    "NamespaceSelectionAgent",
    "NamespaceSelectionAgentConfig",
    "RAGAgent",
    "RAGAgentConfig",
    "RetrievalAgent",
    "RetrievalAgentConfig",
    "WebuiAgent",
    "WebuiAgentConfig",
]
