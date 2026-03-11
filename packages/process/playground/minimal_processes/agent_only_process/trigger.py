import asyncio

from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.processes import ProcessConfig

from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.agents.AgentB.AgentB import AgentB
from playground.minimal_processes.agent_only_process.AgentOnlyProcess import AgentOnlyProcess
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner

enable_logging()


async def main():
    runner_a = AgentTestRunner(
        agent_type=AgentA,
        agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    runner_b = AgentTestRunner(
        agent_type=AgentB,
        agent_config=AgentConfig(
            agent_id="agent_b",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    process_runner = ProcessTestRunner(
        process_type=AgentOnlyProcess,
        process_config=ProcessConfig(
            process_id="agent_only_process",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    async with process_runner.test_run(delay_before_stop=3):
        async with runner_b.test_run(delay_before_stop=3):
            async with runner_a.test_run(delay_before_stop=3) as topic:
                await runner_a.send_event_from_topic(
                    topic=topic,
                    start_event=AgentAStartEvent(payload="Payload by Agent A :)"),
                )


if __name__ == "__main__":
    asyncio.run(main())
