from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.basic.FewShotAgent.FewShowAgentConfig import FewShotAgentConfig
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.steps.prompting.few_shot_step.events.FewShotEvent import FewShotEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.generative_ai.prompting.few_shot.create_few_shot_messages import (
    create_few_shot_messages,
)
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events import StartEvent, StopEvent, ControlEvent, LLMEvent


class LimitChatHistoryWithContextEvent(ControlEvent):
    pass


class FewShotAgent(Agent):
    @step()
    async def start(
            self,
            event: StartEvent,
            agent_config: FewShotAgentConfig,
            run_context: RunContext,
    ) -> FewShotEvent:
        """When StartEvent is received Few Shot Examples are and returned in the FewShotEvent.
        Additionally, the input messages are stored in the RunContext."""
        locale = await run_context.get("locale")
        await run_context.set("messages", event.messages)
        few_shot_messages = create_few_shot_messages(
            agent_config.few_shot.few_shot_examples, locale
        )
        return FewShotEvent(
            few_shot_examples=few_shot_messages,
            few_shot_system_prompt=agent_config.few_shot.few_shot_system_prompt,
        )

    @step
    async def limit_chat_history(
            self, event: FewShotEvent, run_context: RunContext
    ) -> LimitChatHistoryWithContextEvent:
        # TODO: call limit chat history with the few shot examples
        return LimitChatHistoryWithContextEvent()

    @step
    async def right_agent_guard(
            self,
            agent_config: FewShotAgentConfig,
            displayer: EventDisplayer,
    ) -> LLMEvent:
        messages = event.limited_history_with_context
        prompt = PromptTemplate(
            "Extract an invoice from the following text. If you cannot find an invoice ID, use the company name '{company_name}' and the date as the invoice ID: {text}"
        )
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            response = llm.structured_predict(
                Invoice, prompt, text=text, company_name="Uber"
            )

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, messages)

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
