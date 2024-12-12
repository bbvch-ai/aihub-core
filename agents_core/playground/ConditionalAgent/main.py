import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.ConditionalAgent.ConditionalAgent import ConditionalAgent
from playground.ConditionalAgent.ConditionalAgentConfig import ConditionalAgentConfig


async def main():
    runner = AgentTestRunner(
        agent_type=ConditionalAgent,
        agent_config=ConditionalAgentConfig(
            agent_id="conditional_agent",
            name=LocaleString(en="Conditional Agent"),
            description=LocaleString(en="This is an agent with conditions"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(messages=[ChatMessage(content="Hello", role=MessageRole.USER)]),
        )


if __name__ == "__main__":
    asyncio.run(main())