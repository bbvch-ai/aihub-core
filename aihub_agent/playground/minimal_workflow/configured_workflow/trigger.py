import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from playground.minimal_workflow.configured_workflow.ConfiguredAgent import (
    ConfiguredAgent,
)
from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import (
    ConfiguredAgentAgentConfig,
    StartStepConfig,
)


async def main():
    runner = AgentTestRunner(
        agent_type=ConfiguredAgent,
        agent_config=ConfiguredAgentAgentConfig(
            agent_id="configured_agent",
            name=LocaleString(en="Configured Agent"),
            description=LocaleString(en="This is a configured agent"),
            system_prompt=LocaleString(en="You are an agent"),
            some_agent_value="Value on agent config",
            start_step_config=StartStepConfig(some_step_value="Value on step config"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)]
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
