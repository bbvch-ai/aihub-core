import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.FanOutAgent.FanOutAgent import FanOutAgent
from playground.FanOutAgent.FanOutAgentConfig import FanOutAgentConfig


async def main():
    runner = AgentTestRunner(
        agent_type=FanOutAgent,
        agent_config=FanOutAgentConfig(
            agent_id="fan_out_agent",
            name=LocaleString(en="Fan Out Agent"),
            description=LocaleString(en="This is an agent that fans out multiple steps"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(messages=[])
        )

if __name__ == "__main__":
    asyncio.run(main())