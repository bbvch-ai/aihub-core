import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_lib.testing.logging.logger import enable_logging
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
        agent_config=OrchestratorAgentConfig(
            agent_id="orchestrator_agent",
            name=LocaleString(en="Orchestrator Agent"),
            description=LocaleString(en="This is an orchestrator agent"),
            system_prompt=LocaleString(en="You are an orchestrator agent"),
        ),
    )

    worker_runner = AgentTestRunner(
        agent_type=WorkerAgent,
        agent_config=WorkerAgentConfig(
            agent_id="worker_agent",
            name=LocaleString(en="Worker Agent"),
            description=LocaleString(en="This is a worker agent"),
            system_prompt=LocaleString(en="You are a worker agent"),
        ),
    )

    async with worker_runner.test_run(delay_before_stop=5):
        async with orchestrator_runner.test_run(delay_before_stop=3) as topic:
            await orchestrator_runner.send_event_from_topic(
                topic=topic,
                start_event=UserMessageEvent(
                    messages=[ChatMessage(content="128", role=MessageRole.USER)], user=fake_user()
                ),
            )


if __name__ == "__main__":
    asyncio.run(main())
