from typing import ClassVar

from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.events.agent.semantic.llm.LLMStopEvent import LLMStopEvent
from swiss_ai_hub.core.events.agent.semantic.llm.Message import Message
from swiss_ai_hub.core.events.agent.semantic.reranker.RerankerEvent import RerankerEvent
from swiss_ai_hub.core.events.agent.semantic.retriever.RetrieverEvent import RetrieverEvent
from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.testing.milvus_vector_store_content import DEFAULT_DOCUMENTS

from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class SemanticEventAgent(Agent):
    """Agent demonstrating semantic event patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Semantic Event Agent",
        de="Semantischer Event Agent",
        fr="Agent Événement Sémantique",
        it="Agente Evento Semantico",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for semantic event demo",
        de="Agent für semantische Event Demo",
        fr="Agent pour démo événement sémantique",
        it="Agente per demo evento semantico",
    )
    icon: ClassVar[str] = "mage:tag"

    @step()
    async def retriever_step(self, event: StartEvent) -> RetrieverEvent:
        return RetrieverEvent(
            nodes=[IngestedNode.from_llama_index_node(node) for node in DEFAULT_DOCUMENTS],
        )

    @step()
    async def rerank_step(self, event: RetrieverEvent) -> RerankerEvent:
        return RerankerEvent(
            input_nodes=event.nodes,
            output_nodes=event.nodes[::-1],
            query="Which document is more important",
            rerank_model_name="Azure AI Search Reranker",
            top_k=5,
        )

    @step()
    async def llm_step(self, event: RerankerEvent) -> LLMStopEvent:
        return LLMStopEvent(
            input_messages=[
                Message.from_string(
                    role="user",
                    content="Given these documents, what do you want to tell me?",
                )
            ],
            output_messages=[Message.from_string(role="agent", content="Everything is important!")],
            invocation_parameters={"temperature": 0.7},
            chat_model_name="gpt-4o",
            provider="azure",
            token_count_prompt=10,
            token_count_completion=25,
            token_count_total=35,
        )
