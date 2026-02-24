import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.processes.ProcessConfig import ProcessConfig

from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.minimal_processes.human_only_process.HumanOnlyProcess import HumanOnlyProcess

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
