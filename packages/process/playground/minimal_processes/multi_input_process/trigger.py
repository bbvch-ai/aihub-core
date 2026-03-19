from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402
from swiss_ai_hub.core.agents import AgentConfig  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.processes import ProcessConfig  # noqa: E402

from playground.agents.agent_a.agent_a import AgentA  # noqa: E402
from playground.agents.agent_a.events.agent_a_start_event import AgentAStartEvent  # noqa: E402
from playground.agents.agent_b.agent_b import AgentB  # noqa: E402
from playground.agents.agent_c.agent_c import AgentC  # noqa: E402
from playground.minimal_processes.multi_input_process.multi_input_process import MultiInputProcess  # noqa: E402
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

    runner_c = AgentTestRunner(
        agent_type=AgentC,
        agent_config=AgentConfig(
            agent_id="agent_c",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    process_runner = ProcessTestRunner(
        process_type=MultiInputProcess,
        process_config=ProcessConfig(
            process_id="multi_input_process",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )

    async with process_runner.test_run(delay_before_stop=3):
        async with runner_c.test_run(delay_before_stop=3):
            async with runner_b.test_run(delay_before_stop=3):
                async with runner_a.test_run(delay_before_stop=3) as topic:
                    await runner_a.send_event_from_topic(
                        topic=topic,
                        start_event=AgentAStartEvent(payload="Payload by Agent A :)"),
                    )


if __name__ == "__main__":
    asyncio.run(main())
