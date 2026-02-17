import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.processes.ProcessConfig import ProcessConfig

from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.minimal_processes.process_sequence.InitialProcess import InitialProcess
from playground.minimal_processes.process_sequence.SubsequentProcess import SubsequentProcess

enable_logging()


async def main():
    agent_runner_a = AgentTestRunner(
        agent_type=AgentA,
        default_agent_config=AgentConfig(
            agent_id="agent_a",
            agent_class=AgentA.__name__,
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    initial_process_runner = ProcessTestRunner(
        process_type=InitialProcess,
        process_config=ProcessConfig(
            process_id="initial_process",
            process_class=InitialProcess.__name__,
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    subsequent_process_runner = ProcessTestRunner(
        process_type=SubsequentProcess,
        process_config=ProcessConfig(
            process_id="subsequent_process",
            process_class=SubsequentProcess.__name__,
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    async with initial_process_runner.test_run(delay_before_stop=3):
        async with subsequent_process_runner.test_run(delay_before_stop=3):
            async with agent_runner_a.test_run(delay_before_stop=3) as topic:
                await agent_runner_a.send_event_from_topic(
                    topic=topic,
                    start_event=AgentAStartEvent(payload="Payload by Agent A :)"),
                )


if __name__ == "__main__":
    asyncio.run(main())
