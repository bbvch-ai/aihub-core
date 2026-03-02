import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.bounded_loop.BoundedLoopAgent import BoundedLoopAgent
from playground.minimal_workflow.bounded_loop.BoundedLoopAgentConfig import BoundedLoopAgentConfig


async def main():
    runner = AgentTestRunner(
        agent_type=BoundedLoopAgent,
        agent_config=BoundedLoopAgentConfig(
            agent_id="bounded_iterative_loop_agent",
            name=LocaleString(en="Bounded Iterative Agent"),
            description=LocaleString(en="This is an agent that loops"),
            loop_max=2,
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
