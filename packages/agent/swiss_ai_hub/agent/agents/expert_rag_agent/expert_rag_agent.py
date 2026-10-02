from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ExpertRejectEvent,
    FewShotRejectEvent,
    HumanInTheLoop,
    MemoryStorageRequestedEvent,
    RAGFailureReason,
    RAGFailureStopEvent,
    RAGStartEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import format_expert_conversation
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.expert_asking_agent.events.ask_expert_start_event import AskExpertStartEvent
from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.expert_rag_agent.expert_write_namespace import ExpertWriteNamespace
from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.events.user_requests_expert_event import UserRequestsExpertEvent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import generate_follow_up_questions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.rag.answer_hand_back import AnswerHandBack
from swiss_ai_hub.agent.rag.answer_prompt import AnswerPrompt
from swiss_ai_hub.agent.rag.preconditions import (
    check_is_answer_response,
    check_is_no_answer_response,
)
from swiss_ai_hub.agent.rag.step_functions import (
    do_context_block,
    do_finalize_rag_stop,
    do_respond_with_llm,
)
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step


@precondition()
async def is_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a successful answer."""
    return check_is_answer_response(event)


@precondition()
async def is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is an unsuccessful answer."""
    return check_is_no_answer_response(event)


class ExpertRAGAgent(RAGAgent):
    """
    A RAG agent that consults a human expert when the retrieved context is insufficient.

    Everything up to the context-sufficiency verdict is `RAGAgent`, capabilities included. This blueprint
    replaces what happens after an insufficient verdict: instead of answering that it cannot, it asks the
    user for consent, delegates the question to the configured expert-asking agent, and answers from the
    expert's reply as if it were retrieved context. Two inherited steps are overridden for that: the prompt
    takes the expert's reply or the user's refusal to escalate as its outcome, and the answer reports the
    expert outcome in its stop.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.expert_rag_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.expert_rag_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:building-a"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_prompt.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_prompt.description"),
        icon="mdi:database-plus",
    )
    async def assemble_prompt_step(  # type: ignore[override]
        self,
        outcome: ContextSufficientAcceptEvent | FewShotRejectEvent | ExpertRejectEvent | ExpertAnswerContextEvent,
        ctx: Conversation.Contextualized,
        memories: Memory.Recalled,
        files: AttachedFiles.Contents,
        knowledge: Knowledge.Searched,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: ExpertRAGAgentConfig,
        guard_config: ContextSufficientGuardStepConfig,
        t: LocaleHandler,
        documents: InOrderNodeCombinerEvent | None = None,
    ) -> Conversation.ComposeRequest:
        """An insufficient verdict goes to the expert rather than to an answer, so the expert's reply is the
        context when there is one, and a declined escalation answers with the verdict's reason."""
        match outcome:
            case ExpertAnswerContextEvent():
                rejection, context = None, do_context_block(outcome.context_message)
            case ContextSufficientAcceptEvent():
                rejection, context = None, do_context_block(documents.context_message) if documents else []
            case _:
                rejection, context = outcome, []
        return AnswerPrompt.compose(
            rejection,
            context,
            ctx,
            (memories, files, knowledge),
            start_event,
            agent_config.system_prompt,
            guard_config.context_insufficient_prompt,
            t,
        )

    # --- Expert Escalation Steps ---

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.handle_insufficient_context.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.expert_rag_agent.steps.handle_insufficient_context.description"
        ),
        icon="mage:message-check",
    )
    async def insufficient_context_ask_expert_step(
        self,
        _: ContextInsufficientRejectEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.confirmation.request:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.context_not_sufficient"))
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.asking_for_consent"))
        return HumanInTheLoop.confirmation.invoke(question=t("agent.expert_rag_agent.messages.consent_question"))

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.consent_answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.consent_answer.description"),
        icon="mage:message-question-mark",
    )
    async def user_expert_inquiry_response(
        self,
        event: HumanInTheLoop.confirmation.response,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> UserRequestsExpertEvent | ExpertRejectEvent:
        if event.response is True:
            await displayer.display_thought(t("agent.expert_rag_agent.thoughts.user_consented"))
            return UserRequestsExpertEvent()
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.user_declined"))
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.waiting_for_instructions"))
        return ExpertRejectEvent(reason="User declined expert escalation")

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.invoke_expert_agent.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.invoke_expert_agent.description"),
        icon="mage:robot",
    )
    async def forward_to_expert_asking_agent_step(
        self,
        user_message_event: UserMessageEvent | RAGStartEvent,
        ctx: Conversation.Contextualized,
        _: UserRequestsExpertEvent,
        displayer: EventDisplayer,
        agent_config: ExpertRAGAgentConfig,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.forwarding_to_expert"))
        await displayer.display_chunk(
            t("agent.expert_rag_agent.messages.expert_forwarding_confirmation"),
            model_name=ExpertRAGAgent.__name__,
        )
        await displayer.display_chunk(
            "\n",
            model_name=ExpertRAGAgent.__name__,
        )
        await displayer.display_chunk(
            t("agent.expert_rag_agent.messages.expert_answer_coming_soon"),
            model_name=ExpertRAGAgent.__name__,
        )
        return AgentInTheLoop.invoke(
            agent_class=agent_config.expert_escalation.agent.agent_class,
            agent_id=agent_config.expert_escalation.agent.agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=ctx.query,
                locale=user_message_event.locale,
                user=user_message_event.user,
                org_memory_namespace=ExpertWriteNamespace.resolve(user_message_event, agent_config.org_memory),
            ),
        )

    @step(
        precondition=is_answer_response,
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_positive.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_positive.description"),
        icon="mage:user-check",
    )
    async def expert_answered_step(
        self,
        displayer: EventDisplayer,
        event: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> ExpertAnswerContextEvent:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.expert_answered"))
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.can_answer_question"))

        expert_conversation = event.stop_event.expert_conversation
        expert_conversation_text = format_expert_conversation(expert_conversation)

        context_content = t("agent.prompt.expert_context", expert_conversation=expert_conversation_text)
        await displayer.display_thought(f"Expert context: {context_content}")

        context_message = ChatMessage(role=MessageRole.SYSTEM, content=context_content)
        return ExpertAnswerContextEvent(context_message=context_message)

    @step(
        precondition=is_no_answer_response,
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_negative.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_negative.description"),
        icon="mage:user-cross",
    )
    async def expert_not_answered_step(
        self,
        displayer: EventDisplayer,
        _: AgentInTheLoop.response,
        user_message_event: UserMessageEvent | RAGStartEvent,
        agent_config: ExpertRAGAgentConfig,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> RAGFailureStopEvent:
        await displayer.display_thought(t("agent.expert_rag_agent.thoughts.expert_unable_to_answer"))
        unable_to_answer_message = t("agent.expert_rag_agent.messages.expert_unable_to_answer")
        await displayer.display_chunk(
            unable_to_answer_message,
            model_name=ExpertRAGAgent.__name__,
        )
        # The spine's title step already fired on the query event; only follow-ups are missing on this
        # decline path, grounded on the canned decline message as the "answer".
        await generate_follow_up_questions(
            [*user_message_event.messages, ChatMessage(role=MessageRole.ASSISTANT, content=unable_to_answer_message)],
            agent_config.task_llm,
            displayer,
            t,
            user,
        )
        return RAGFailureStopEvent(reason=RAGFailureReason.EXPERT_DECLINED, answer=unable_to_answer_message)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_error.name"),
        description=AgentLocaleString.from_i18n_path("agent.expert_rag_agent.steps.expert_answer_error.description"),
        icon="mage:exclamation-circle",
    )
    async def expert_exception_step(
        self,
        displayer: EventDisplayer,
        exception_event: AgentInTheLoop.exception,
        user_message_event: UserMessageEvent | RAGStartEvent,
        agent_config: ExpertRAGAgentConfig,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> RAGFailureStopEvent:
        await displayer.display_thought(
            t(
                "agent.expert_rag_agent.thoughts.expert_error",
                error_code=exception_event.exception_event.http_status_code,
                error_message=exception_event.exception_event.message,
            )
        )
        error_occurred_message = t("agent.expert_rag_agent.messages.expert_error_occurred")
        await displayer.display_chunk(
            error_occurred_message,
            model_name=ExpertRAGAgent.__name__,
        )
        # The spine's title step already fired on the query event; only follow-ups are missing on this
        # error path, grounded on the canned error message as the "answer".
        await generate_follow_up_questions(
            [*user_message_event.messages, ChatMessage(role=MessageRole.ASSISTANT, content=error_occurred_message)],
            agent_config.task_llm,
            displayer,
            t,
            user,
        )
        return RAGFailureStopEvent(reason=RAGFailureReason.EXPERT_ERRORED, answer=error_occurred_message)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.name"),
        description=AgentLocaleString.from_i18n_path("agent.rag_agent.steps.respond_with_llm.description"),
        icon="mage:message",
    )
    async def respond_with_llm_step(  # type: ignore[override]
        self,
        outcome: ContextSufficientAcceptEvent | FewShotRejectEvent | ExpertRejectEvent | ExpertAnswerContextEvent,
        composed: Conversation.Composed,
        ctx: Conversation.Contextualized,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        topic: AgentInstanceTopic,
        t: LocaleHandler,
        context_insufficient_reject: ContextInsufficientRejectEvent | None = None,
        user: UserIdentity | None = None,
    ) -> list[MemoryStorageRequestedEvent | Conversation.CompleteRequest]:
        """An expert's answer counts as a successful grounding, while a declined escalation keeps the verdict."""
        answer = await do_respond_with_llm(composed.history, agent_config.llm, displayer, t, user, as_stop_step=False)
        stop = do_finalize_rag_stop(
            llm_event=answer,
            expert_answer_context=outcome if isinstance(outcome, ExpertAnswerContextEvent) else None,
            few_shot_reject=outcome if isinstance(outcome, FewShotRejectEvent) else None,
            context_insufficient_reject=context_insufficient_reject,
        )
        return AnswerHandBack.of(ctx, answer, stop, agent_config, topic, t, user)
