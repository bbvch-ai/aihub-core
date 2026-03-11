import asyncio

from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.performance.PerformanceTestingAgent.PerformanceTestingAgent import PerformanceTestingAgent
from playground.performance.PerformanceTestingAgent.PerformanceTestingAgentConfig import PerformanceTestingAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=PerformanceTestingAgent,
        agent_config=PerformanceTestingAgentConfig(
            agent_id="performance_testing_agent",
            name=LocaleString(en="Performance Testing Agent"),
            description=LocaleString(en=""),
            number_of_events=10,
            payload_kb=0,
        ),
    )

    async with runner.test_run(delay_before_stop=1) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(),
        )


if __name__ == "__main__":
    asyncio.run(main())
