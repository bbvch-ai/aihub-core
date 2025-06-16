import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging
from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.minimal_processes.agent_only_process.AgentA.AgentA import AgentA
from playground.minimal_processes.agent_only_process.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.minimal_processes.agent_only_process.AgentB.AgentB import AgentB
from playground.minimal_processes.agent_only_process.AgentOnlyProcess import AgentOnlyProcess

enable_logging()


async def main():
    runner_a = AgentTestRunner(
        agent_type=AgentA,
        agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    runner_b = AgentTestRunner(
        agent_type=AgentB,
        agent_config=AgentConfig(
            agent_id="agent_b",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    process_runner = ProcessTestRunner(
        process_type=AgentOnlyProcess,
        process_id="agent_only_process",
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
