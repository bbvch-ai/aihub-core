from typing import ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
from aihub_lib.nats.events.memory.store.StoreOrganizationMemoryEvent import StoreOrganizationMemoryEvent
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from llama_index.core.prompts import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerInsufficientEvent import ExpertAnswerInsufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerSufficientEvent import ExpertAnswerSufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.i18n.AgentLocaleString import AgentLocaleString
from aihub_agent.workflow.decorators.step import step


class ExpertAskingAgent(Agent):
    """
    The expert asking agent receives an expert question as input and poses the question to a dedicated
    Slack or Teams channel.
    The agent validates the answer and poses follow-up questions until the answer is sufficient.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.expert_asking_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.expert_asking_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:building-a"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.steps.invoke_expert.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.steps.invoke_expert.description"),
        icon="mage:users",
    )
    async def start_step(
        self,
        question_event: AskExpertStartEvent | AskExpertEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: AgentLocaleHandler,
    ) -> BotInTheLoop.request:
        await displayer.display_thought(
            t("agent.expert_asking_agent.thoughts.asking_question", question=question_event.question_to_expert)
        )

        chat_history = await run_context.get("chat_history", [])
        chat_history = [ChatMessage(**message) for message in chat_history]
        chat_history.append(ChatMessage(role=MessageRole.ASSISTANT, content=question_event.question_to_expert))
        await run_context.set("chat_history", [msg.model_dump() for msg in chat_history])

        return BotInTheLoop.invoke(
            question=question_event.question_to_expert,
            user=question_event.user,
            channel_config=agent_config.get_active_channel_config(),
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.steps.expert_response.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.steps.expert_response.description"),
        icon="mage:message-question-mark",
    )
    async def expert_response_step(
        self,
        initial_question_event: AskExpertStartEvent,
        expert_response_event: BotInTheLoop.response,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: AgentLocaleHandler,
    ) -> RouterEvent:
        expert_response = expert_response_event.response
        expert_user_id = expert_response_event.responder.user_id
        expert_name = expert_response_event.responder.user_name
        await displayer.display_thought(
            t("agent.expert_asking_agent.thoughts.expert_responded", response=expert_response)
        )

        loop_count = await run_context.get("loop_count", 0)
        await run_context.set("loop_count", loop_count + 1)

        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]
        chat_history.append(ChatMessage(role=MessageRole.USER, content=expert_response))
        await run_context.set("chat_history", [msg.model_dump() for msg in chat_history])

        instructions = RichPromptTemplate(
            template_str=t("lib.prompt.router.instructions.expert_answer_sufficient"),
        ).format(chat_history=chat_history, query=initial_question_event.question_to_expert)

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await route_to_event_using_llm(
                instructions=instructions,
                routes=[
                    RouteOptions.for_event(
                        ExpertAnswerSufficientEvent(
                            response=expert_response,
                            expert_user_id=expert_user_id,
                            expert_name=expert_name,
                        ),
                        t("agent.expert_asking_agent.routes.answer_sufficient"),
                    ),
                    RouteOptions.for_event(
                        ExpertAnswerInsufficientEvent(
                            response=expert_response,
                            expert_user_id=expert_user_id,
                            expert_name=expert_name,
                        ),
                        t("agent.expert_asking_agent.routes.answer_insufficient"),
                    ),
                ],
                t=t,
                llm=llm,
            )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.steps.response_sufficient_router.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.expert_asking_agent.steps.response_sufficient_router.description"
        ),
        icon="mage:message",
    )
    async def router_step(
        self,
        initial_question_event: AskExpertStartEvent,
        router_event: RouterEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        thread_context: ThreadContext,
        memory: AgentMemory,
        topic: AgentInstanceTopic,
        t: AgentLocaleHandler,
    ) -> AnswerStopEvent | ExpertAnswerInsufficientEvent:
        await displayer.display_thought(t("agent.expert_asking_agent.thoughts.determine_sufficient"))
        event = router_event.selected_option.event
        if isinstance(event, ExpertAnswerSufficientEvent):
            await displayer.display_thought(t("agent.expert_asking_agent.thoughts.answer_sufficient"))
            chat_history = await run_context.get("chat_history", [])
            chat_history = [ChatMessage(**message) for message in chat_history]

            # Store expert conversation as organization memory
            memory_text = f"Question: {initial_question_event.question_to_expert}\n\nExpert Answer: {event.response}"
            memory_added = await memory.add_organization_memory(
                memory=memory_text,
                user_id=initial_question_event.user.id,
                thread_id=topic.thread_id,
                display_id=topic.display_id,
                run_id=topic.run_id,
                tenant_id=agent_config.tenant_id,
                tenant_namespace=agent_config.tenant_namespace,
            )

            # Emit event for observability
            await displayer.display_event(
                StoreOrganizationMemoryEvent.from_memory_added_object(memory_added=memory_added)
            )

            return AnswerStopEvent(expert_answer=event.response, expert_conversation=chat_history)
        return event

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.steps.follow_up_question.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.steps.follow_up_question.description"),
        icon="mage:user-cross",
    )
    async def follow_up_question(
        self,
        initial_question_event: AskExpertStartEvent,
        _: ExpertAnswerInsufficientEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        t: AgentLocaleHandler,
        run_context: RunContext,
    ) -> AskExpertEvent | NoAnswerStopEvent:
        loop_count = await run_context.get("loop_count", 0)
        if loop_count >= agent_config.loop_max:
            await displayer.display_thought(t("agent.expert_asking_agent.thoughts.max_questions_reached"))
            await displayer.display_thought(t("agent.expert_asking_agent.thoughts.returning_insufficient"))
            return NoAnswerStopEvent()

        await displayer.display_thought(t("agent.expert_asking_agent.thoughts.answer_not_sufficient"))
        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            chat = RichPromptTemplate(template_str=t("agent.expert_asking_agent.follow_up_question")).format_messages(
                chat_history=chat_history,
                question=initial_question_event.question_to_expert,
            )
            response: ChatResponse = await llm.achat(chat)
            return AskExpertEvent(
                question_to_expert=response.message.content,
                locale=initial_question_event.locale,
                user=initial_question_event.user,
            )
