from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AgentSuitabilityAcceptEvent,
    AgentSuitabilityRejectEvent,
    LimitChatHistoryEvent,
    LLMStopEvent,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    agent_description_guard,
    condense_standalone_question,
    create_few_shot_messages,
    limit_chat_history,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_event import FewShotEvent
from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_standalone_question_condenser_event import (
    FewShotStandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class FewShotAgent(Agent):
    """
    Implements a Few Shot Agent.

    The FewShotAgent orchestrates steps to safeguard the request against the agent description,
    and then produce an output based on fewShotExamples.

    ### Features
    - Guard the request against the agent description.
    - Create Message History with Few Shot Examples and Condensed User Question.
    - Generate responses using an LLM based on the context (Few Shot Examples).
    ...
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.few_shot_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.few_shot_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:book"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.limit_chat_history.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.limit_chat_history.description"),
        icon="mage:edit",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: FewShotAgentConfig,
    ) -> LimitChatHistoryEvent:
        """
        Truncates incoming chat messages to fit within the configured token limit
        """
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.agent_suitability_guard.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.agent_suitability_guard.description"),
        icon="mage:shield-check",
    )
    async def right_agent_guard(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent,
        t: LocaleHandler,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
    ) -> AgentSuitabilityAcceptEvent | AgentSuitabilityRejectEvent:
        messages = event.limited_history
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            guard_result = await agent_description_guard(
                agent_description=agent_config.description,
                llm=llm,
                t=t,
                user_query=start_event.user_query,
                messages=messages,
            )
        if not guard_result.success:
            return AgentSuitabilityRejectEvent(reason=guard_result.reasoning)
        return AgentSuitabilityAcceptEvent(
            reason=guard_result.reasoning,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.condense_standalone_question.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.few_shot_agent.steps.condense_standalone_question.description"
        ),
        icon="mage:archive",
    )
    async def condense_standalone_question_step(
        self,
        _: AgentSuitabilityAcceptEvent,
        start_event: UserMessageEvent,
        chat_history_event: LimitChatHistoryEvent,
        agent_config: FewShotAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> FewShotStandaloneQuestionCondenserEvent:
        """
        Condenses the chat history and user query into a standalone question.
        """
        await displayer.display_thought(t("agent.thought.condense_question"))

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            condensed_question = condense_standalone_question(
                chat_history=chat_history_event.limited_history,
                message=start_event.last_user_message,
                t=t,
                llm=llm,
            )
            return FewShotStandaloneQuestionCondenserEvent(condensed_chat_message=condensed_question)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.create_few_shot_examples.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.create_few_shot_examples.description"),
        icon="mage:checklist",
    )
    async def create_few_shot_examples(
        self,
        event: FewShotStandaloneQuestionCondenserEvent,
        start_event: UserMessageEvent,
        chat_history_event: LimitChatHistoryEvent,
        agent_config: FewShotAgentConfig,
    ) -> FewShotEvent:
        """
        Creates a few shot examples from the agent configuration and creates the context for the llm call
        including the system messages, the few shot examples and the condensed user Message.
        Important: The normal chat history is not used directly (only regarded in the condensed question),
        as the few shot examples are used instead. Same applies to the original user message
        """
        locale = start_event.locale
        few_shot_messages = create_few_shot_messages(agent_config.few_shot.few_shot_examples, locale)
        chat_history = chat_history_event.limited_history
        system_messages = [msg for msg in chat_history if msg.role == MessageRole.SYSTEM]
        system_prompt = ChatMessage(
            role=MessageRole.SYSTEM, content=agent_config.few_shot.system_prompt.in_locale(locale)
        )
        context = [
            *system_messages,
            system_prompt,
            *few_shot_messages,
            event.condensed_chat_message,
        ]
        return FewShotEvent(
            few_shot_examples=few_shot_messages,
            system_prompt=system_prompt,
            full_context=context,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.respond_with_llm.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.respond_with_llm.description"),
        icon="mage:message",
    )
    async def respond_with_llm_step(
        self,
        event: FewShotEvent,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thread_context: ThreadContext,
    ) -> LLMStopEvent:
        """
        Generates a response using the configured LLM.
        """
        await displayer.display_thought(t("agent.thought.write_answer_based_on_few_shot_examples"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            stop_event = await displayer.display_llm_stream(
                agent_config.llm, llm, event.full_context, as_stop_step=True
            )

        return stop_event

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.stop.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.stop.description"),
        icon="mage:cancel",
    )
    async def stop_step(self, _: AgentSuitabilityRejectEvent) -> StopEvent:
        return StopEvent()
