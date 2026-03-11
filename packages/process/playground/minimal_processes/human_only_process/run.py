import asyncio

from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.processes import ProcessConfig

from playground.minimal_processes.human_only_process.HumanOnlyProcess import HumanOnlyProcess
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner

enable_logging()


async def main():
    process_runner = ProcessTestRunner(
        process_type=HumanOnlyProcess,
        process_config=ProcessConfig(
            process_id="human_only_process",
            name=LocaleString(en="..."),
            description=LocaleString(en="..."),
        ),
    )
    await process_runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
