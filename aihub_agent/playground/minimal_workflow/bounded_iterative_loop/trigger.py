import asyncio
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from playground.minimal_workflow.bounded_iterative_loop.BoundedIterativeLoopAgent import BoundedIterativeLoopAgent
from playground.minimal_workflow.bounded_iterative_loop.BoundedIterativeLoopAgentConfig import \
    BoundedIterativeLoopAgentConfig


async def main():
    runner = AgentTestRunner(
        agent_type=BoundedIterativeLoopAgent,
        agent_config=BoundedIterativeLoopAgentConfig(
            agent_id="bounded_iterative_loop_agent",
            name=LocaleString(en="Bounded Iterative Agent"),
            description=LocaleString(en="This is an agent that loops"),
            system_prompt=LocaleString(en="You are an agent"),
            loop_max=2
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)], user=fake_user()
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
