# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    AllowedBucketConfig,
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.NamespaceSelectionAgent import NamespaceSelectionAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=NamespaceSelectionAgent,
        default_agent_config=NamespaceSelectionAgentConfig(
            agent_class=NamespaceSelectionAgent.__name__,
            agent_id="dev_namespace_selection_agent",
            name=LocaleString(en="Dev Namespace Selection Agent"),
            description=LocaleString(en="Development config for NamespaceSelectionAgent"),
            selection_llm=LLMConfig(
                model_name="text-generation/nano",
            ),
            allowed_buckets=[
                AllowedBucketConfig(bucket_name="default", retrieve_k=5),
            ],
            rag_agent_class="RAGAgent",
            rag_agent_id="dev_rag_agent",
            max_correction_rounds=2,
            allow_topic_change=True,
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
