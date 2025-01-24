import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from playground.minimal_workflow.semantic_workflow.SemanticEventAgent import (
    SemanticEventAgent,
)
from playground.minimal_workflow.semantic_workflow.SemanticEventAgentConfig import (
    SemanticEventAgentConfig,
)


async def main():
    runner = AgentTestRunner(
        agent_type=SemanticEventAgent,
        agent_config=SemanticEventAgentConfig(
            agent_id="semantic_event_agent",
            name=LocaleString(en="Semantic Event Agent"),
            description=LocaleString(en="This is an agent with semantic events"),
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
