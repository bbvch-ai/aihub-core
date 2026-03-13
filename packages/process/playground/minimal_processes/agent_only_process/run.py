from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402
from swiss_ai_hub.core.agents import AgentConfig  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.processes import ProcessConfig  # noqa: E402

from playground.agents.agent_a.agent_a import AgentA  # noqa: E402
from playground.agents.agent_b.agent_b import AgentB  # noqa: E402
from playground.minimal_processes.agent_only_process.agent_only_process import AgentOnlyProcess  # noqa: E402
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner  # noqa: E402

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

    await asyncio.gather(
        process_runner.run_forever(),
        runner_a.run_forever(),
        runner_b.run_forever(),
    )


if __name__ == "__main__":
    asyncio.run(main())
