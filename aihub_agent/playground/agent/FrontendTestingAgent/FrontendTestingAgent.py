from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import (
    UserMessageEvent,
    EmbeddingEvent,
    RetrieverEvent,
    RerankerEvent,
    ToolEvent,
    StopEvent,
    AgentInTheLoop,
    HumanInTheLoop,
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
)

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from aihub_lib.nats.events.semantic import Embedding
from aihub_lib.nats.events.semantic.guard import GuardEvent
from aihub_lib.nats.events.semantic.retriever import Document
from aihub_lib.persistence.rag.vectors.node_metadata import DOCUMENT_TITLE, SOURCE, CREATED_AT, REFERENCE_URL
from playground.agent.FrontendTestingAgent.events.FrontendTestingEventA import FrontendTestingEventA
from playground.agent.FrontendTestingAgent.events.FrontendTestingEventB import FrontendTestingEventB


class CustomHumanInTheLoopRequestEvent(HumanInTheLoopRequestEvent):
    pass


class CustomHumanInTheLoopResponseEvent(HumanInTheLoopResponseEvent):
    pass


class CustomHumanInTheLoop(HumanInTheLoop):
    request = CustomHumanInTheLoopRequestEvent
    response = CustomHumanInTheLoopResponseEvent


class FrontendTestingAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        print("[OrchestratorAgent.start_step]", event)
        return AgentInTheLoop.invoke(agent_id="dev_agent", agent_class="LLMWrappingAgent", start_event=event)

    @step()
    async def guard_step(self, _: AgentInTheLoop.response) -> GuardEvent:
        return GuardEvent()

    @step()
    async def router_step(self, _: GuardEvent) -> RouterEvent:
        routes = [
            RouteOptions(name="Route A", description="Good Route", instructions="Select This", event=FrontendTestingEventA()),
            RouteOptions(name="Route B", description="Bad Route", instructions="Not this", event=FrontendTestingEventB()),
        ]
        return RouterEvent(
            routes=routes,
            selected_option=routes[0],
            reason="I just took the first one tbh"
        )

    @step()
    async def unpack_router_step(self, event: RouterEvent) -> FrontendTestingEventA:
        return event.selected_option.event

    @step()
    async def embedding_step(self, _: FrontendTestingEventA, displayer: EventDisplayer) -> EmbeddingEvent:
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
    async def retriever_step(self, _: EmbeddingEvent) -> RetrieverEvent:
        return RetrieverEvent(
            documents=[
                Document(
                    id="1",
                    content="Der Zug hat Verspätung!",
                    score=0.9,
                    metadata={
                        DOCUMENT_TITLE: "SBB",
                        SOURCE: "sbb.docx",
                        CREATED_AT: 1743681278,
                        REFERENCE_URL: "https://www.sbb.ch",
                    },
                ),
                Document(
                    id="2",
                    content="Corona is not real!",
                    score=0.85,
                    metadata={
                        DOCUMENT_TITLE: "WHO Bericht",
                        SOURCE: "who.pdf",
                        CREATED_AT: 1743481278,
                        REFERENCE_URL: "https://www.who.int",
                    },
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
    async def tool(self, _: RerankerEvent) -> ToolEvent:
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
    async def hitl_step(self, _: ToolEvent) -> CustomHumanInTheLoop.request:
        print("[HumanInTheLoopAgent.start_step]")
        return CustomHumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def botl_start(self, user_message_event: UserMessageEvent, hitl_event: CustomHumanInTheLoop.response, displayer: EventDisplayer) -> BotInTheLoop.request:
        await displayer.display_chunk(content=f"Hitl Response: {hitl_event.response}", model_name="FrontendTestingAgent")
        print("Bot in the loop")
        return BotInTheLoop.invoke(
            user=user_message_event.user,
            question="Make some noise",
            slack_channel_id="C08MK7Z8GU9",
        )

    @step()
    async def stop(self, event: BotInTheLoop.response, displayer: EventDisplayer) -> StopEvent:
        await displayer.display_chunk(content=f"Botl Response: {event.response}", model_name="FrontendTestingAgent")
        return StopEvent()
