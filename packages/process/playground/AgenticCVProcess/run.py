import asyncio

from swiss_ai_hub.core.infrastructure import enable_logging

from playground.AgenticCVProcess.AgenticCVProcess import AgenticCVProcess
from playground.AgenticCVProcess.AgenticCVProcessConfig import AgenticCVProcessConfig
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner

enable_logging()


async def main():
    process_runner = ProcessTestRunner(
        process_type=AgenticCVProcess,
        process_config=AgenticCVProcessConfig.as_form(),
    )
    await process_runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
