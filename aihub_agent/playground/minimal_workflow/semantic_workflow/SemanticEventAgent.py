from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, RerankerEvent, RetrieverEvent, LLMStopEvent
from aihub_lib.nats.events.semantic import Message
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.testing.milvus_vector_store_content import DEFAULT_DOCUMENTS


class SemanticEventAgent(Agent):
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
