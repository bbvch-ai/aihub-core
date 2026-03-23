from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.agentic_cv_process.agentic_cv_process import AgenticCVProcess  # noqa: E402
from playground.agentic_cv_process.agentic_cv_process_config import AgenticCVProcessConfig  # noqa: E402
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner  # noqa: E402

enable_logging()


async def main():
    process_runner = ProcessTestRunner(
        process_type=AgenticCVProcess,
        process_config=AgenticCVProcessConfig.as_form(),
    )
    await process_runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
