from aihub_agent.agents.basic.FewShotAgent.events.FewShotEvent import FewShotEvent
from aihub_agent.agents.basic.FewShotAgent.events.RightAgentEvent import RightAgentEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.i18n import LocaleHandler
from llama_index.core.base.llms.types import MessageRole

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.basic.FewShotAgent.FewShowAgentConfig import FewShotAgentConfig
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.decorators.step import step
from aihub_lib.generative_ai.guards.agent_description_guard import agent_description_guard

from aihub_lib.generative_ai.prompting.few_shot.create_few_shot_messages import (
    create_few_shot_messages,
)
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events import StartEvent, StopEvent, ControlEvent, LLMEvent, UserMessageEvent


class LimitChatHistoryWithContextEvent(ControlEvent):
    pass


class PromptTemplate:
    pass


class FewShotAgent(Agent):
    """
    Implements a Few Shot Agent.

    ...
    """

    @step()
    async def limit_chat_history_step(
            self,
            event: StartEvent | UserMessageEvent,
            agent_config: FewShotAgentConfig,
            run_context: RunContext,
    ) -> LimitChatHistoryEvent:
        """
        Truncates incoming chat messages to fit within the configured token limit
        """
        user_messages = [msg for msg in event.messages if msg.role == MessageRole.USER]
        try:
            await run_context.set("user_query", user_messages[-1].content)
        except IndexError:
            raise ValueError("No user messages found in the event.")
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        serialized_chat_history = [msg.model_dump() for msg in limited_chat_history]
        await run_context.set("chat_history", serialized_chat_history)

        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step
    async def right_agent_guard(
            self,
            event: LimitChatHistoryEvent,
            agent_config: FewShotAgentConfig,
            displayer: EventDisplayer,
            t: LocaleHandler,
            run_context: RunContext,
    ) -> RightAgentEvent | StopEvent:
        messages = event.limited_history_with_context
        user_query = await run_context.get("user_query")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            guard_result = await agent_description_guard(
                agent_description=agent_config.description,
                llm=llm,
                t=t,
                user_query=user_query,
                messages=messages,
            )
        if not guard_result.success:
            async with agent_config.llm.cost_reporting_llm(displayer) as llm:
                prompt = PromptTemplate(t("lib.guards.agent_description_guard"))
                await displayer.display_llm_stream(agent_config.llm, llm, messages)
            return StopEvent()
        return RightAgentEvent(
            success=guard_result.success,
            reasoning=guard_result.reasoning,
        )

    @step()
    async def create_few_shot_examples(
            self,
            event: RightAgentEvent,
            agent_config: FewShotAgentConfig,
            run_context: RunContext,
    ) -> FewShotEvent:
        """
        When RightAgentEvent is received Few Shot Examples are and returned in the FewShotEvent.
        Additionally, the input messages are stored in the RunContext.
        """
        locale = await run_context.get("locale")
        few_shot_messages = create_few_shot_messages(agent_config.few_shot.few_shot_examples, locale)
        return FewShotEvent(
            few_shot_examples=few_shot_messages,
            few_shot_system_prompt=agent_config.few_shot.few_shot_system_prompt,
        )

    @step
    async def ask_llm(
            self,
            event: LimitChatHistoryWithContextEvent,
            agent_config: FewShotAgentConfig,
            displayer: EventDisplayer,
    ) -> LLMEvent:
        messages = event.limited_history_with_context
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, messages)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
