import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.processes.ProcessConfig import ProcessConfig

from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.agents.AgentA.AgentA import AgentA
from playground.agents.AgentB.AgentB import AgentB
from playground.minimal_processes.agent_only_process.AgentOnlyProcess import AgentOnlyProcess

enable_logging()


async def main():
    runner_a = AgentTestRunner(
        agent_type=AgentA,
        default_agent_config=AgentConfig(
            agent_id="agent_a",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    runner_b = AgentTestRunner(
        agent_type=AgentB,
        default_agent_config=AgentConfig(
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

    await asyncio.gather(
        process_runner.run_forever(),
        runner_a.run_forever(),
        runner_b.run_forever(),
    )


if __name__ == "__main__":
    asyncio.run(main())
