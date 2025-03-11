from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.guards.agent_description_guard import agent_description_guard
from aihub_lib.generative_ai.prompting.few_shot.create_few_shot_messages import create_few_shot_messages
from aihub_lib.generative_ai.utils.condense_standalone_question import condense_standalone_question
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import GuardRejectionEvent, LLMEvent, StopEvent, UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.basic.FewShotAgent.events.FewShotEvent import FewShotEvent
from aihub_agent.agents.basic.FewShotAgent.events.FewShotStandaloneQuestionCondenserEvent import (
    FewShotStandaloneQuestionCondenserEvent,
)
from aihub_agent.agents.basic.FewShotAgent.events.RightAgentEvent import RightAgentEvent
from aihub_agent.agents.basic.FewShotAgent.FewShowAgentConfig import FewShotAgentConfig
from aihub_agent.agents.common.events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.workflow.decorators.step import step


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

    @step()
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

    @step()
    async def right_agent_guard(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent,
        t: LocaleHandler,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
    ) -> RightAgentEvent | GuardRejectionEvent:
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
            return GuardRejectionEvent(reason=guard_result.reasoning)
        return RightAgentEvent(
            success=guard_result.success,
            reasoning=guard_result.reasoning,
        )

    @step()
    async def condense_standalone_question_step(
        self,
        _: RightAgentEvent,
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
                message=start_event.user_query,
                t=t,
                llm=llm,
                condense_prompt=agent_config.condense_question_prompt,
            )
            return FewShotStandaloneQuestionCondenserEvent(condensed_chat_message=condensed_question)

    @step()
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
        few_shot_system_prompt = ChatMessage(
            role=MessageRole.SYSTEM, content=agent_config.few_shot.few_shot_system_prompt.in_locale(locale)
        )
        context = [
            *system_messages,
            few_shot_system_prompt,
            *few_shot_messages,
            event.condensed_chat_message,
        ]
        return FewShotEvent(
            few_shot_examples=few_shot_messages,
            few_shot_system_prompt=few_shot_system_prompt,
            full_context=context,
        )

    @step()
    async def respond_with_llm_step(
        self,
        event: FewShotEvent,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMEvent:
        """
        Generates a response using the configured LLM.
        """
        await displayer.display_thought(t("agent.thought.write_answer_based_on_few_shot_examples"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.full_context)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
