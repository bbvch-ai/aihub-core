# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip  # noqa: E402
from playground.minimal_workflow.organization_memory_workflow.organization_memory_agent import (  # noqa: E402
    OrganizationMemoryAgent,
)
from playground.minimal_workflow.organization_memory_workflow.organization_memory_agent_config import (  # noqa: E402
    OrganizationMemoryAgentConfig,
)

AihubInstrumentor().instrument()

import asyncio  # noqa: E402

from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()


async def main():
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
                model_name="text-generation/gpt-oss-120b",
                default_parameter=LLMParameter(temperature=1.0),
            ),
            tenant_id="default_tenant",
            tenant_namespace="default_namespace",
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
