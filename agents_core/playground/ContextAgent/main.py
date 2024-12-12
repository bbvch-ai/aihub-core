import asyncio
import logging
from asyncio import sleep

from bson import ObjectId

from agents_core.runners.AgentRunner import AgentRunner
from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from playground.ContextAgent.ContextAgent import ContextAgent
from playground.ContextAgent.ContextAgentConfig import ContextAgentConfig
from playground.ContextAgent.Events.CustomStartEvent import CustomStartEvent


THREAD_ID = "6756ddb05c399b888009a559"

async def main():
    runner = AgentTestRunner(
        agent_type=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            name=LocaleString(en="Context Agent"),
            description=LocaleString(en="This is an agent that accesses the run and thread context"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=CustomStartEvent(payload="This is some payload"),
        )


if __name__ == "__main__":
    asyncio.run(main())