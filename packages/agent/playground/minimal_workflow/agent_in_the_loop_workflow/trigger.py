from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from llama_index.core.base.llms.types import ChatMessage, MessageRole  # noqa: E402
from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings  # noqa: E402
from swiss_ai_hub.core.events.agent import UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.minimal_workflow.agent_in_the_loop_workflow.orchestrator_agent.orchestrator_agent import (  # noqa: E402
    OrchestratorAgent,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.orchestrator_agent.orchestrator_agent_config import (  # noqa: E402
    OrchestratorAgentConfig,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.worker_agent.worker_agent import WorkerAgent  # noqa: E402
from playground.minimal_workflow.agent_in_the_loop_workflow.worker_agent.worker_agent_config import (  # noqa: E402
    WorkerAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()


async def main():
    orchestrator_runner = AgentTestRunner(
        agent_type=OrchestratorAgent,
        agent_config=OrchestratorAgentConfig(
            agent_id="orchestrator_agent",
            agent_class=OrchestratorAgent.__name__,
            name=LocaleString(en="Orchestrator Agent"),
            description=LocaleString(en="This is an orchestrator agent"),
        ),
    )

    worker_runner = AgentTestRunner(
        agent_type=WorkerAgent,
        agent_config=WorkerAgentConfig(
            agent_id="worker_agent",
            agent_class=WorkerAgent.__name__,
            name=LocaleString(en="Worker Agent"),
            description=LocaleString(en="This is a worker agent"),
        ),
    )

    async with worker_runner.test_run(delay_before_stop=5):
        async with orchestrator_runner.test_run(delay_before_stop=3) as topic:
            await orchestrator_runner.send_event_from_topic(
                topic=topic,
                start_event=UserMessageEvent(
                    messages=[ChatMessage(content="128", role=MessageRole.USER)],
                    user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                ),
            )


if __name__ == "__main__":
    asyncio.run(main())
