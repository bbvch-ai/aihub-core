from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.processes import ProcessConfig  # noqa: E402

from playground.minimal_processes.human_only_process.human_only_process import HumanOnlyProcess  # noqa: E402
from swiss_ai_hub.process.runners.process_test_runner import ProcessTestRunner  # noqa: E402

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
