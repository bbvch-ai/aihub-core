from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import LLMEvent, LLMStopEvent, UserMessageEvent, EmbeddingEvent, RetrieverEvent, \
    RerankerEvent, ToolEvent, StopEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events.semantic import Embedding
from aihub_lib.nats.events.semantic.retriever import Document
from playground.agent.FrontendTestingAgent.FrontendTestingAgentConfig import FrontendTestingAgentConfig


class FrontendTestingAgent(Agent):
    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: FrontendTestingAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        await displayer.display_thought("First, I answer the user")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages)

    @step()
    async def guard_step(self, event: LLMEvent, displayer: EventDisplayer) -> EmbeddingEvent:
        await displayer.display_thought("Now I need to check the guard")
        return EmbeddingEvent(
            text="This is the text that was embedded",
            embedding_model_name="text-embedding-ada-002",
            embeddings=[
                Embedding(
                    text="This is the text that was embedded",
                    vector=[0.1, 0.2, 0.3],
                )
            ],
        )

    @step()
    async def retriever_step(self, event: EmbeddingEvent) -> RetrieverEvent:
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
    async def tool(self, event: RerankerEvent) -> ToolEvent:
        return ToolEvent(
            name="Weather Tool",
            description="Fetches the current weather",
            json_schema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get the weather for.",
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "description": "Units of measurement.",
                    },
                },
                "required": ["location"],
            },
            parameters={
                "location": "New York",
                "units": "metric",
            },
        )

    @step()
    async def stop(self, event: ToolEvent) -> LLMStopEvent:
        return StopEvent()
