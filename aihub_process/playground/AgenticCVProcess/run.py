import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.AgenticCVProcess.AgenticCVProcess import AgenticCVProcess

enable_logging()


async def main():
    process_runner = ProcessTestRunner(
        process_type=AgenticCVProcess,
        default_process_config=ProcessConfig(
            process_id="agentic_cv_process",
            process_class=AgenticCVProcess.__name__,
            name=LocaleString(en="Agentic CV Process"),
            description=LocaleString(en="Models the process of reviewing and accepting a CV"),
        ),
    )
    await process_runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
