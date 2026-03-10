import asyncio

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.nats.events import StartEvent

from playground.minimal_workflow.conditional_workflow.ConditionalAgent import (
    ConditionalAgent,
)
from playground.minimal_workflow.conditional_workflow.ConditionalAgentConfig import (
    ConditionalAgentConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ConditionalAgent,
        agent_config=ConditionalAgentConfig(
            agent_id="conditional_agent",
            agent_class=ConditionalAgent.__name__,
            name=LocaleString(en="Conditional Agent"),
            description=LocaleString(en="This is an agent with conditions"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(),
        )


if __name__ == "__main__":
    asyncio.run(main())
