import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.nats.events.user.UserMessageEvent import UserMessageEvent

from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.OrchestratorAgent import OrchestratorAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.OrchestratorAgentConfig import (
    OrchestratorAgentConfig,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.WorkerAgent import WorkerAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.WorkerAgentConfig import WorkerAgentConfig
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

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
