from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.events.agent import UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import fake_user  # noqa: E402

from playground.minimal_workflow.organization_memory_workflow.organization_memory_agent import (  # noqa: E402
    OrganizationMemoryAgent,
)
from playground.minimal_workflow.organization_memory_workflow.organization_memory_agent_config import (  # noqa: E402
    OrganizationMemoryAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402


async def main():
    """One-shot test runner for OrganizationMemoryAgent."""
    runner = AgentTestRunner(
        agent_type=OrganizationMemoryAgent,
        agent_config=OrganizationMemoryAgentConfig(
            agent_class=OrganizationMemoryAgent.__name__,
            agent_id="org_memory_agent",
            name=LocaleString(en="Organization Memory Agent"),
            description=LocaleString(
                en="Agent for storing and retrieving explicit organizational facts shared across all users"
            ),
            llm=LLMConfig(
                model_name="text-generation/Qwen3-VL-235B-A22B-Instruct",
                default_parameter=LLMParameter(temperature=1.0),
            ),
            tenant_id="default_tenant",
            tenant_namespace="default_namespace",
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[],
                user=fake_user(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
