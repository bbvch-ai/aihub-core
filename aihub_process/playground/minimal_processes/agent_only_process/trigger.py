import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.processes.ProcessConfig import ProcessConfig

from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.agents.AgentB.AgentB import AgentB
from playground.minimal_processes.agent_only_process.AgentOnlyProcess import AgentOnlyProcess

enable_logging()


async def main():
    runner_a = AgentTestRunner(
        agent_type=AgentA,
        default_agent_config=AgentConfig(
            agent_id="agent_a",
            agent_class=AgentA.__name__,
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    runner_b = AgentTestRunner(
        agent_type=AgentB,
        default_agent_config=AgentConfig(
            agent_id="agent_b",
            agent_class=AgentB.__name__,
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    process_runner = ProcessTestRunner(
        process_type=AgentOnlyProcess,
        default_process_config=ProcessConfig(
            process_id="agent_only_process",
            process_class=AgentOnlyProcess.__name__,
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
