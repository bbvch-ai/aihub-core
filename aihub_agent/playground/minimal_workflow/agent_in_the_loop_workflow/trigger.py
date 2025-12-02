import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.infrastructure.logging.logger import enable_logging
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.OrchestratorAgent import OrchestratorAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.OrchestratorAgentConfig import (
    OrchestratorAgentConfig,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.WorkerAgent import WorkerAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.WorkerAgentConfig import WorkerAgentConfig

enable_logging()


async def main():
    orchestrator_runner = AgentTestRunner(
        agent_type=OrchestratorAgent,
        default_agent_config=OrchestratorAgentConfig(
            agent_id="orchestrator_agent",
            agent_class=OrchestratorAgent.__name__,
            name=LocaleString(en="Orchestrator Agent"),
            description=LocaleString(en="This is an orchestrator agent"),
        ),
    )

    worker_runner = AgentTestRunner(
        agent_type=WorkerAgent,
        default_agent_config=WorkerAgentConfig(
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
