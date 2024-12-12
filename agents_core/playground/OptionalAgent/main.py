import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.OptionalAgent.OptionalAgent import OptionalAgent
from playground.OptionalAgent.OptionalAgentConfig import OptionalAgentConfig



async def main():
    runner = AgentTestRunner(
        agent_type=OptionalAgent,
        agent_config=OptionalAgentConfig(
            agent_id="optional_agent",
            name=LocaleString(en="Optional Agent"),
            description=LocaleString(en="This is an agent with optional input"),
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