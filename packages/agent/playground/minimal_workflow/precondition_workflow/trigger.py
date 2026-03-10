import asyncio

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent

from playground.minimal_workflow.precondition_workflow.PreconditionAgent import PreconditionAgent
from playground.minimal_workflow.precondition_workflow.PreconditionAgentConfig import PreconditionAgentConfig
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=PreconditionAgent,
        agent_config=PreconditionAgentConfig(
            agent_id="precondition_agent",
            agent_class=PreconditionAgent.__name__,
            name=LocaleString(en="Agent with preconditions"),
            description=LocaleString(en="This is an agent that has preconditions"),
            number_of_events=10,
        ),
    )
    async with runner.test_run(delay_before_stop=5) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=StartEvent())


if __name__ == "__main__":
    asyncio.run(main())
