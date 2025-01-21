from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, RerankerEvent, RetrieverEvent
from aihub_lib.nats.events.semantic import Message
from aihub_lib.nats.events.semantic.retriever import Document
from playground.minimal_workflow.semantic_workflow.events.LLMStopEvent import (
    LLMStopEvent,
)


class SemanticEventAgent(Agent):
    @step()
    async def retriever_step(self, event: StartEvent) -> RetrieverEvent:
        return RetrieverEvent(
            documents=[
                Document(
                    id="1",
                    content="This is the Content of some important Document!",
                    score=0.9,
                    metadata={"title": "Must Read"},
                ),
                Document(
                    id="2",
                    content="This is even more important content!",
                    score=0.85,
                    metadata={"title": "Must-must Read"},
                ),
            ],
        )

    @step()
    async def rerank_step(self, event: RetrieverEvent) -> RerankerEvent:
        return RerankerEvent(
            input_documents=event.documents,
            output_documents=event.documents[::-1],
            query="Which document is more important",
            rerank_model_name="Azure AI Search Reranker",
            top_k=5,
        )

    @step()
    async def llm_step(self, event: RerankerEvent) -> LLMStopEvent:
        return LLMStopEvent(
            input_messages=[
                Message(
                    role="user",
                    content="Given these documents, what do you want to tell me?",
                )
            ],
            output_messages=[Message(role="agent", content="Everything is important!")],
            invocation_parameters={"temperature": 0.7},
            chat_model_name="gpt-4o",
            provider="azure",
            token_count_prompt=10,
            token_count_completion=25,
            token_count_total=35,
        )
