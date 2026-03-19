from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent, StopEvent, UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.llama_index_workflow.llama_index_agent_config import (
    LlamaIndexAgentConfig,
)
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class LlamaIndexAgent(Agent):
    """Agent demonstrating LlamaIndex integration patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="LlamaIndex Agent", de="LlamaIndex Agent", fr="Agent LlamaIndex", it="Agente LlamaIndex"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for LlamaIndex demo",
        de="Agent für LlamaIndex Demo",
        fr="Agent pour démo LlamaIndex",
        it="Agente per demo LlamaIndex",
    )
    icon: ClassVar[str] = "mage:light-bulb"

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: LlamaIndexAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        print("[LlamaIndexAgent.start_step]")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
