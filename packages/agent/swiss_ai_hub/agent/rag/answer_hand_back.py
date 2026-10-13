from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import LLMEvent, MemoryStorageRequestedEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.memory.memory import Memory


class AnswerHandBack:
    """How a RAG answer leaves the blueprint: remembered, then completed with its outcome."""

    @staticmethod
    def of(
        ctx: Conversation.Contextualized,
        answer: LLMEvent,
        stop: StopEvent,
        agent_config: RAGAgentConfig,
        topic: AgentInstanceTopic,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> list[MemoryStorageRequestedEvent | Conversation.CompleteRequest]:
        """The memory delegation first, so it is published before the run tears down, and the completion last."""
        remember = Memory.remember(
            query=ctx.query,
            answer=answer,
            user=user,
            topic=topic,
            agent_config=agent_config,
            memory=agent_config,
            locale=t.locale,
        )
        return [*([remember] if remember else []), Conversation.complete(answer=answer, stop=stop)]
