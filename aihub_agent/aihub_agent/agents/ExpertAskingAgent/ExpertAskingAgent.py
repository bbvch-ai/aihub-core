from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import AgentInTheLoop, ExpertInTheLoop
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from aihub_lib.persistence.insight.InsightEntity import InsightCreator, InsightEntity, InsightSource
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from llama_index.core.prompts import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerInsufficientEvent import ExpertAnswerInsufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerSufficientEvent import ExpertAnswerSufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.KnowledgeSnippetEvent import KnowledgeSnippetEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.TriggerInsightAgentEvent import TriggerInsightAgentEvent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.agents.InsightAgent.events.InsightStartEvent import InsightStartEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.workflow.decorators.step import step


class ExpertAskingAgent(Agent):
    """
    The expert asking agent receives an expert question as input and poses the question to a dedicated slack
    channel.
    The agent validates the answer and poses follow-up question until the answer is sufficient, in which
    case it creates a knowledge snippet and saves it to the knowledge base.
    """

    async def _get_context_from_run(self, run_context: RunContext) -> tuple[list[ChatMessage], list[IngestedNode]]:
        """Helper method to retrieve chat history and nodes from run context."""
        chat_history_data = await run_context.get("chat_history", [])
        chat_history = [ChatMessage(**msg) for msg in chat_history_data]
        nodes_data = await run_context.get("nodes", [])
        nodes = [IngestedNode(**node) for node in nodes_data]
        return chat_history, nodes

    @step(
        name=LocaleString(en="Invoke Expert Step"),
        description=LocaleString(en="Poses question to a group of experts."),
        icon="material-symbols:group-rounded",
    )
    async def start_step(
        self,
        question_event: AskExpertStartEvent | AskExpertEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        thread_context: ThreadContext,
        t: AgentLocaleHandler,
    ) -> BotInTheLoop.request | ExpertInTheLoop.request:
        await displayer.display_thought(
            t("agent.expert_asking_agent.thoughts.asking_question", question=question_event.question_to_expert)
        )

        # Store nodes in run_context for later use (only on start event)
        if isinstance(question_event, AskExpertStartEvent) and question_event.nodes:
            await run_context.set("nodes", [node.model_dump() for node in question_event.nodes])

        chat_history = await run_context.get("chat_history", [])
        chat_history = [ChatMessage(**message) for message in chat_history]
        chat_history.append(ChatMessage(role=MessageRole.ASSISTANT, content=question_event.question_to_expert))
        await run_context.set("chat_history", [msg.model_dump() for msg in chat_history])

        if agent_config.expert_channel_type == "gui":
            return await self._invoke_expert_gui(
                question_event=question_event,
                agent_config=agent_config,
                run_context=run_context,
            )

        return BotInTheLoop.invoke(
            question=question_event.question_to_expert,
            user=question_event.user,
            slack_channel_id=agent_config.slack_channel_id,
        )

    async def _invoke_expert_gui(
        self,
        question_event: AskExpertStartEvent | AskExpertEvent,
        agent_config: ExpertAskingAgentConfig,
        run_context: RunContext,
    ) -> ExpertInTheLoop.request:
        """Creates an ExpertInTheLoop request for GUI-based expert input.

        Note: The ExpertInTheLoopRequestEvent is persisted to MongoDB by the API
        (via ExpertQuestionPersister subscriber), not by the agent.
        """
        nodes_data = await run_context.get("nodes", [])
        context_str = None
        if nodes_data:
            nodes = [IngestedNode(**node) for node in nodes_data]
            context_str = "\n\n".join([node.content for node in nodes if node.content])

        # Prefer expert_group from event (set by parent agent) over agent config
        expert_group = question_event.expert_group or agent_config.expert_group

        return ExpertInTheLoop.invoke(
            user=question_event.user,
            question=question_event.question_to_expert,
            context=context_str,
            expert_group=expert_group,
            priority="normal",
            locale=question_event.locale,
        )

    @step(
        name=LocaleString(en="Expert Response (BitL)"),
        description=LocaleString(en="Processes the expert response from Bot-in-the-Loop."),
        icon="carbon:question-answering",
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
        expert_name = expert_response_event.responder.user_name if expert_response_event.responder else "Unknown Expert"
        return await self._process_expert_response(
            initial_question_event=initial_question_event,
            expert_response=expert_response,
            expert_name=expert_name,
            agent_config=agent_config,
            displayer=displayer,
            run_context=run_context,
            t=t,
        )

    @step(
        name=LocaleString(en="Expert Response (GUI)"),
        description=LocaleString(en="Processes the expert response from GUI interface."),
        icon="carbon:question-answering",
    )
    async def expert_gui_response_step(
        self,
        initial_question_event: AskExpertStartEvent,
        expert_response_event: ExpertInTheLoop.response,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: AgentLocaleHandler,
    ) -> RouterEvent:
        expert_response = expert_response_event.response
        expert_name = expert_response_event.responder.user_name if expert_response_event.responder else "Unknown Expert"
        return await self._process_expert_response(
            initial_question_event=initial_question_event,
            expert_response=expert_response,
            expert_name=expert_name,
            agent_config=agent_config,
            displayer=displayer,
            run_context=run_context,
            t=t,
        )

    async def _process_expert_response(
        self,
        initial_question_event: AskExpertStartEvent,
        expert_response: str,
        expert_name: str,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: AgentLocaleHandler,
    ) -> RouterEvent:
        """Common logic for processing expert responses from either BitL or GUI."""
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
                        ExpertAnswerSufficientEvent(response=expert_response, expert_name=expert_name),
                        "Choose this option if the experts response sufficiently answered the question.",
                    ),
                    RouteOptions.for_event(
                        ExpertAnswerInsufficientEvent(response=expert_response, expert_name=expert_name),
                        "Choose this option if the experts response does NOT sufficiently answered the question.",
                    ),
                ],
                t=t,
                llm=llm,
            )

    @step(
        name=LocaleString(en="Response Sufficient Router"),
        description=LocaleString(en="Checks whether the expert has sufficiently answerd the question yet."),
        icon="line-md:chat",
    )
    async def router_step(
        self,
        router_event: RouterEvent,
        displayer: EventDisplayer,
        t: AgentLocaleHandler,
    ) -> ExpertAnswerSufficientEvent | ExpertAnswerInsufficientEvent:
        await displayer.display_thought(t("agent.expert_asking_agent.thoughts.determine_sufficient"))
        return router_event.selected_option.event

    @step(
        name=LocaleString(en="Generate knowledge"),
        description=LocaleString(en="Create a new knowledge snippet that can be safed to knowledge database."),
        icon="ix:user-success-filled",
    )
    async def create_knowledge_snippet(
        self,
        initial_question_event: AskExpertStartEvent,
        _: ExpertAnswerSufficientEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        t: AgentLocaleHandler,
        run_context: RunContext,
    ) -> KnowledgeSnippetEvent:
        await displayer.display_thought(t("agent.expert_asking_agent.thoughts.answer_sufficient"))

        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            chat = RichPromptTemplate(
                template_str=t("agent.expert_asking_agent.knowledge_snippet_prompt")
            ).format_messages(
                chat_history=chat_history,
                question=initial_question_event.question_to_expert,
            )
            response: ChatResponse = await llm.achat(chat)
            return KnowledgeSnippetEvent(content=response.message.content)

    @step(
        name=LocaleString(en="Save knowledge"),
        description=LocaleString(en="Persists knowledge into the knowledge database."),
        icon="bi:database-up",
    )
    async def save_knowledge_snippet(
        self,
        initial_question_event: AskExpertStartEvent,
        knowledge_snippet_event: KnowledgeSnippetEvent,
        expert_answer_event: ExpertAnswerSufficientEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        t: AgentLocaleHandler,
        thread_context: ThreadContext,
        run_context: RunContext,
    ) -> TriggerInsightAgentEvent:
        await displayer.display_thought(t("agent.expert_asking_agent.thoughts.saving_knowledge"))

        # Create insight source information
        source = InsightSource(
            thread_id=thread_context.thread_id,
            expert_name=expert_answer_event.expert_name,
        )

        # Create insight creator information
        creator = InsightCreator(
            agent_class=agent_config.agent_class,
            agent_id=agent_config.agent_id,
            user_id=initial_question_event.user.id if initial_question_event.user else None,
            user_name=initial_question_event.user.name if initial_question_event.user else None,
        )

        # Generate a title from the question
        title = initial_question_event.question_to_expert[:100]
        if len(initial_question_event.question_to_expert) > 100:
            title = title[:97] + "..."

        # Store insight in MongoDB
        insight = InsightEntity.create_insight(
            title=title,
            content=knowledge_snippet_event.content,
            question=initial_question_event.question_to_expert,
            expert_answer=expert_answer_event.response,
            namespace=agent_config.insight_namespace,
            source=source,
            creator=creator,
        )

        await displayer.display_thought(
            t("agent.expert_asking_agent.thoughts.knowledge_saved", filename=str(insight.id))
        )
        return TriggerInsightAgentEvent(expert_answer=knowledge_snippet_event.content)

    @step(
        name=LocaleString(en="Trigger Insight Agent"),
        description=LocaleString(en="Triggers the InsightAgent to process the expert conversation."),
        icon="carbon:data-enrichment",
    )
    async def trigger_insight_agent_step(
        self,
        trigger_event: TriggerInsightAgentEvent,
        initial_question_event: AskExpertStartEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: AgentLocaleHandler,
    ) -> AgentInTheLoop.request | AnswerStopEvent:
        chat_history, nodes = await self._get_context_from_run(run_context)

        # If InsightAgent is configured, trigger it asynchronously
        if agent_config.insight_agent_class and agent_config.insight_agent_id:
            await displayer.display_thought(t("agent.expert_asking_agent.thoughts.triggering_insight_agent"))
            return AgentInTheLoop.invoke(
                agent_class=agent_config.insight_agent_class,
                agent_id=agent_config.insight_agent_id,
                start_event=InsightStartEvent(
                    chat_history=chat_history,
                    nodes=nodes,
                    question=initial_question_event.question_to_expert,
                    expert_answer=trigger_event.expert_answer,
                    locale=initial_question_event.locale,
                ),
                share_thread_id=False,
                share_display_id=False,
            )

        # If InsightAgent is not configured, return answer directly
        return AnswerStopEvent(
            expert_answer=trigger_event.expert_answer,
            chat_history=chat_history,
            nodes=nodes,
        )

    @step(
        name=LocaleString(en="Insight Agent Complete"),
        description=LocaleString(en="Handles InsightAgent completion and returns final answer."),
        icon="ix:user-success-filled",
    )
    async def insight_agent_complete_step(
        self,
        _: AgentInTheLoop.response,
        trigger_event: TriggerInsightAgentEvent,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: AgentLocaleHandler,
    ) -> AnswerStopEvent:
        await displayer.display_thought(t("agent.expert_asking_agent.thoughts.insight_agent_complete"))
        chat_history, nodes = await self._get_context_from_run(run_context)

        return AnswerStopEvent(
            expert_answer=trigger_event.expert_answer,
            chat_history=chat_history,
            nodes=nodes,
        )

    @step(
        name=LocaleString(en="Insight Agent Error"),
        description=LocaleString(en="Handles InsightAgent error and returns answer despite the error."),
        icon="ix:error",
    )
    async def insight_agent_exception_step(
        self,
        exception_event: AgentInTheLoop.exception,
        trigger_event: TriggerInsightAgentEvent,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: AgentLocaleHandler,
    ) -> AnswerStopEvent:
        await displayer.display_thought(
            t(
                "agent.expert_asking_agent.thoughts.insight_agent_error",
                error_code=exception_event.exception_event.http_status_code,
                error_message=exception_event.exception_event.message,
            )
        )
        chat_history, nodes = await self._get_context_from_run(run_context)

        # Return answer despite InsightAgent error - the knowledge was already saved
        return AnswerStopEvent(
            expert_answer=trigger_event.expert_answer,
            chat_history=chat_history,
            nodes=nodes,
        )

    @step(
        name=LocaleString(en="Follow up question"),
        description=LocaleString(en="Poses follow up question to expert as answer is not sufficient yet."),
        icon="ix:user-fail-filled",
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
