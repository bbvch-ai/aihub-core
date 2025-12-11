import asyncio
import random

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    AgentInTheLoop,
    EmbeddingEvent,
    ExceptionEvent,
    RerankerEvent,
    RetrieverEvent,
    StopEvent,
    ToolEvent,
    UserMessageEvent,
)
from aihub_lib.nats.events.common import LanguageEvent, LimitChatHistoryEvent, StandaloneQuestionCondenserEvent
from aihub_lib.nats.events.display import ChunkEvent, ThoughtEvent
from aihub_lib.nats.events.guard import (
    AgentSuitabilityAcceptEvent,
    AgentSuitabilityRejectEvent,
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    SensitiveInfoAcceptEvent,
    SensitiveInfoRejectEvent,
)
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from aihub_lib.nats.events.semantic import Embedding
from aihub_lib.nats.events.semantic.guard import GuardEvent
from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_ID,
    DOCUMENT_TITLE,
    NAMESPACE,
    REFERENCE_URL,
    SOURCE,
)
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.schema import NodeWithScore, TextNode

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.agent.FrontendTestingAgent.events.FrontendTestingEventA import FrontendTestingEventA
from playground.agent.FrontendTestingAgent.events.FrontendTestingEventB import FrontendTestingEventB


class CustomHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class CustomHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class CustomHumanInTheLoop(HumanInTheLoopInput):
    request = CustomHumanInTheLoopRequestEvent
    response = CustomHumanInTheLoopResponseEvent


class FrontendTestingAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request | ExceptionEvent:
        if random.random() > 0.95:
            return ExceptionEvent(message="5% chance that this occurs :)", http_status_code=500)
        print("[OrchestratorAgent.start_step]", event)
        event.agent_config = None
        return AgentInTheLoop.invoke(agent_id="dev_agent", agent_class="LLMWrappingAgent", start_event=event)

    @step()
    async def guard_step(self, _: AgentInTheLoop.response, displayer: EventDisplayer) -> GuardEvent:
        await asyncio.sleep(1)
        return GuardEvent()

    @step()
    async def sensitive_info_check(self, _: GuardEvent) -> SensitiveInfoAcceptEvent | SensitiveInfoRejectEvent:
        # Randomly accept or reject for demonstration - high acceptance rate to show more events
        if random.random() > 0.05:  # 95% acceptance rate
            return SensitiveInfoAcceptEvent(reason="No sensitive information detected in the content")
        return SensitiveInfoRejectEvent(
            reason="Potential sensitive information detected", cleaned_answer="[Content Redacted for Privacy]"
        )

    @step()
    async def context_suitability_check(
        self, _: SensitiveInfoAcceptEvent
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent:
        if random.random() > 0.05:  # 95% acceptance rate
            return ContextSufficientAcceptEvent(reason="Sufficient context available for accurate response")
        return ContextInsufficientRejectEvent(reason="Insufficient context to provide accurate answer", new_query=None)

    @step()
    async def agent_suitability_check(
        self, _: ContextSufficientAcceptEvent
    ) -> AgentSuitabilityAcceptEvent | AgentSuitabilityRejectEvent:
        if random.random() > 0.05:  # 95% acceptance rate
            return AgentSuitabilityAcceptEvent(reason="Agent is suitable for this type of request")
        return AgentSuitabilityRejectEvent(
            reason="Agent not suitable for this request type",
        )

    @step()
    async def few_shot_evaluation(self, _: AgentSuitabilityAcceptEvent) -> FewShotAcceptEvent | FewShotRejectEvent:
        if random.random() > 0.05:  # 95% acceptance rate
            return FewShotAcceptEvent(reason="Few-shot examples are relevant and helpful")
        return FewShotRejectEvent(
            reason="Few-shot examples not suitable for this query",
        )

    @step()
    async def display_thought_process(self, _: FewShotAcceptEvent) -> ThoughtEvent:
        await asyncio.sleep(0.5)
        return ThoughtEvent(
            reasoning_content="I'm analyzing the user's request and considering the best approach to provide a "
            "comprehensive answer."
        )

    @step()
    async def display_chunk_processing(self, _: ThoughtEvent) -> ChunkEvent:
        await asyncio.sleep(0.5)
        return ChunkEvent(
            content="Processing information step by step to ensure accuracy...", model_name="FrontendTestingAgent"
        )

    @step()
    async def language_detection(self, _: ChunkEvent) -> LanguageEvent:
        await asyncio.sleep(0.3)
        languages = ["en", "de", "fr", "it"]
        return LanguageEvent(language_short_name=random.choice(languages))

    @step()
    async def chat_history_limit(self, _: LanguageEvent) -> LimitChatHistoryEvent:
        return LimitChatHistoryEvent(
            limited_history=[
                ChatMessage(role="user", content="Hello, how are you?"),
                ChatMessage(role="assistant", content="I'm doing well, thank you!"),
                ChatMessage(role="user", content="What can you help me with?"),
            ]
        )

    @step()
    async def question_condenser(self, _: LimitChatHistoryEvent) -> StandaloneQuestionCondenserEvent:
        return StandaloneQuestionCondenserEvent(
            condensed_chat_message=ChatMessage(role="user", content="What is the capital of France?")
        )

    @step()
    async def router_step(self, _: StandaloneQuestionCondenserEvent) -> RouterEvent:
        await asyncio.sleep(1)
        routes = [
            RouteOptions(
                name="Route A",
                description="Good Route",
                instructions="Select This",
                event=FrontendTestingEventA(
                    display_name=LocaleString(en="Custom Name Event A"),
                    display_description=LocaleString(en="This is a custom description for Event A"),
                ),
            ),
            RouteOptions(
                name="Route B", description="Bad Route", instructions="Not this", event=FrontendTestingEventB()
            ),
        ]
        return RouterEvent(routes=routes, selected_option=routes[0], reason="I just took the first one tbh")

    @step()
    async def unpack_router_step(self, event: RouterEvent) -> FrontendTestingEventA:
        return event.selected_option.event

    @step()
    async def embedding_step(self, _: FrontendTestingEventA) -> EmbeddingEvent:
        await asyncio.sleep(1)
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
        await asyncio.sleep(1)
        return RetrieverEvent(
            nodes=[
                IngestedNode.from_llama_index_node_with_score(
                    NodeWithScore(
                        score=0.9,
                        node=TextNode(
                            text="Der Zug hat Verspätung!",
                            metadata={
                                DOCUMENT_ID: "1",
                                DOCUMENT_TITLE: "SBB",
                                SOURCE: "sbb.docx",
                                NAMESPACE: "sbb",
                                CREATED_AT: 1743681278,
                                REFERENCE_URL: "https://www.sbb.ch",
                            },
                        ),
                    )
                ),
                IngestedNode.from_llama_index_node_with_score(
                    NodeWithScore(
                        score=0.9,
                        node=TextNode(
                            text="Corona is not real!",
                            metadata={
                                DOCUMENT_ID: "2",
                                DOCUMENT_TITLE: "WHO Bericht",
                                SOURCE: "who.pdf",
                                NAMESPACE: "who",
                                CREATED_AT: 1743481278,
                                REFERENCE_URL: "https://www.who.int",
                            },
                        ),
                    )
                ),
            ],
        )

    @step()
    async def rerank_step(self, event: RetrieverEvent) -> RerankerEvent:
        await asyncio.sleep(1)
        return RerankerEvent(
            input_nodes=event.nodes,
            output_nodes=event.nodes[::-1],
            query="Which document is more important",
            rerank_model_name="Azure AI Search Reranker",
            top_k=5,
        )

    @step()
    async def tool(self, _: RerankerEvent) -> ToolEvent:
        await asyncio.sleep(1)
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
        await asyncio.sleep(1)
        return CustomHumanInTheLoop.invoke(question="Shall I continue?")

    # @step()
    # async def botl_start(
    #     self,
    #     user_message_event: UserMessageEvent,
    #     hitl_event: CustomHumanInTheLoop.response,
    #     displayer: EventDisplayer
    # ) -> BotInTheLoop.request:
    #     await displayer.display_chunk(
    #         content=f"Hitl Response: {hitl_event.response}", model_name="FrontendTestingAgent"
    #     )
    #     print("Bot in the loop")
    #     return BotInTheLoop.invoke(
    #         user=user_message_event.user,
    #         question="Make some noise",
    #         slack_channel_id="C08MK7Z8GU9",
    #     )

    # Error handling steps for rejection events
    @step()
    async def handle_sensitive_info_rejection(
        self, event: SensitiveInfoRejectEvent, displayer: EventDisplayer
    ) -> StopEvent:
        await displayer.display_chunk(
            content=f"Request blocked due to sensitive information: {event.reason}", model_name="FrontendTestingAgent"
        )
        return StopEvent()

    @step()
    async def handle_context_insufficient_rejection(
        self, event: ContextInsufficientRejectEvent, displayer: EventDisplayer
    ) -> StopEvent:
        await displayer.display_chunk(content=f"Cannot proceed: {event.reason}", model_name="FrontendTestingAgent")
        return StopEvent()

    @step()
    async def handle_agent_suitability_rejection(
        self, event: AgentSuitabilityRejectEvent, displayer: EventDisplayer
    ) -> StopEvent:
        await displayer.display_chunk(content=f"Agent not suitable: {event.reason}", model_name="FrontendTestingAgent")
        return StopEvent()

    @step()
    async def handle_few_shot_rejection(self, event: FewShotRejectEvent, displayer: EventDisplayer) -> StopEvent:
        await displayer.display_chunk(
            content=f"Few-shot evaluation failed: {event.reason}", model_name="FrontendTestingAgent"
        )
        return StopEvent()

    @step()
    async def stop(self, event: CustomHumanInTheLoop.response, displayer: EventDisplayer) -> StopEvent:
        await asyncio.sleep(1)
        await displayer.display_chunk(content=f"Hitl Response: {event.response}", model_name="FrontendTestingAgent")
        # await displayer.display_chunk(content=f"Botl Response: {event.response}", model_name="FrontendTestingAgent")
        return StopEvent()
