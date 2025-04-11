import asyncio
import datetime

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.open_webui.sdk import OpenWebuiClient
from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from llama_index.core.prompts import RichPromptTemplate
from stringcase import alphanumcase

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertEvent import AskExpertEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerInsufficientEvent import ExpertAnswerInsufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.ExpertAnswerSufficientEvent import ExpertAnswerSufficientEvent
from aihub_agent.agents.ExpertAskingAgent.events.KnowledgeSnippetEvent import KnowledgeSnippetEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.workflow.decorators.step import step


class ExpertAskingAgent(Agent):
    """
    The expert asking agent receives an expert question as input and poses the question to a dedicated slack
    channel.
    The agent validates the answer and poses follow-up question until the answer is sufficient, in which
    case it creates a knowledge snippet and saves it to the knowledge base.
    """

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
        t: AgentLocaleHandler,
    ) -> BotInTheLoop.request:
        await displayer.display_thought(
            t("agents.expert_asking_agent.thoughts.asking_question", question=question_event.question_to_expert)
        )

        chat_history = await run_context.get("chat_history", [])
        chat_history = [ChatMessage(**message) for message in chat_history]
        chat_history.append(ChatMessage(role=MessageRole.ASSISTANT, content=question_event.question_to_expert))
        await run_context.set("chat_history", [msg.model_dump() for msg in chat_history])

        return BotInTheLoop.invoke(
            question=question_event.question_to_expert,
            user=question_event.user,
            slack_channel_id=agent_config.slack_channel_id,
        )

    @step(
        name=LocaleString(en="Expert Response"),
        description=LocaleString(en="Processes the expert response."),
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
        expert_name = expert_response_event.responder.user_name
        await displayer.display_thought(
            t("agents.expert_asking_agent.thoughts.expert_responded", response=expert_response)
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
        await displayer.display_thought(t("agents.expert_asking_agent.thoughts.determine_sufficient"))
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
        await displayer.display_thought(t("agents.expert_asking_agent.thoughts.answer_sufficient"))

        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            chat = RichPromptTemplate(
                template_str=t("agents.expert_asking_agent.knowledge_snippet_prompt")
            ).format_messages(
                chat_history=chat_history,
                question=initial_question_event.question_to_expert,
            )
            response: ChatResponse = await llm.achat(chat)
            return KnowledgeSnippetEvent(content=response.message.content)

    @step(
        name=LocaleString(en="Safe knowledge"),
        description=LocaleString(en="Persists knowledge into the knowledge database."),
        icon="bi:database-up",
    )
    async def safe_knowledge_snippet(
        self,
        knowledge_snippet_event: KnowledgeSnippetEvent,
        expert_answer_event: ExpertAnswerSufficientEvent,
        agent_config: ExpertAskingAgentConfig,
        displayer: EventDisplayer,
        t: AgentLocaleHandler,
    ) -> AnswerStopEvent:
        await displayer.display_thought(t("agents.expert_asking_agent.thoughts.saving_knowledge"))
        client = OpenWebuiClient(
            base_url=agent_config.open_webui_api_url,
            token=agent_config.open_webui_api_key,
        )
        knowledge_snippet = t(
            "agents.expert_asking_agent.knowledge_snippet",
            content=knowledge_snippet_event.content,
            expert_name=expert_answer_event.expert_name,
            date=datetime.datetime.now().strftime("%Y.%m.%d"),
            time=datetime.datetime.now().strftime("%H:%M:%S"),
        )
        bytes_content = knowledge_snippet.encode("utf-8")
        current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        expert_name = alphanumcase(expert_answer_event.expert_name)
        filename = f"{expert_name}_{current_date_str}.txt"
        file_response = await client.files.upload_file(
            file=bytes_content,
            filename=filename,
        )
        await displayer.display_thought(t("agents.expert_asking_agent.thoughts.knowledge_saved", filename=filename))
        await asyncio.sleep(1)
        await client.knowledge.add_file_to_knowledge(
            knowledge_id=agent_config.open_webui_knowledge_id,
            file_id=file_response.id,
        )
        return AnswerStopEvent(expert_answer=knowledge_snippet)

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
            await displayer.display_thought(t("agents.expert_asking_agent.thoughts.max_questions_reached"))
            await displayer.display_thought(t("agents.expert_asking_agent.thoughts.returning_insufficient"))
            return NoAnswerStopEvent()

        await displayer.display_thought(t("agents.expert_asking_agent.thoughts.answer_not_sufficient"))
        chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage(**message) for message in chat_history]

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            chat = RichPromptTemplate(template_str=t("agents.expert_asking_agent.follow_up_question")).format_messages(
                chat_history=chat_history,
                question=initial_question_event.question_to_expert,
            )
            response: ChatResponse = await llm.achat(chat)
            return AskExpertEvent(
                question_to_expert=response.message.content,
                locale=initial_question_event.locale,
                user=initial_question_event.user,
            )
