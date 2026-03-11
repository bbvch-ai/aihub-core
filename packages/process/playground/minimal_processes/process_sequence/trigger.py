import asyncio

from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.processes import ProcessConfig

from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentA.events.AgentAStartEvent import AgentAStartEvent
from playground.minimal_processes.process_sequence.InitialProcess import InitialProcess
from playground.minimal_processes.process_sequence.SubsequentProcess import SubsequentProcess
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner

enable_logging()


async def main():
    agent_runner_a = AgentTestRunner(
        agent_type=AgentA,
        agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    initial_process_runner = ProcessTestRunner(
        process_type=InitialProcess,
        process_config=ProcessConfig(
            process_id="initial_process",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    subsequent_process_runner = ProcessTestRunner(
        process_type=SubsequentProcess,
        process_config=ProcessConfig(
            process_id="subsequent_process",
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
