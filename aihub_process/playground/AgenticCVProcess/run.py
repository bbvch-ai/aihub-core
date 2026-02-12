import asyncio

from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_process.runners.ProcessTestRunner import ProcessTestRunner
from playground.AgenticCVProcess.AgenticCVProcess import AgenticCVProcess
from playground.AgenticCVProcess.AgenticCVProcessConfig import AgenticCVProcessConfig

enable_logging()


async def main():
    process_runner = ProcessTestRunner(
        process_type=AgenticCVProcess,
        process_config=AgenticCVProcessConfig.as_form(),
    )
    await process_runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
