import asyncio

from aihub_agent.agents.rag.RAGAgent import RAGAgent
from aihub_agent.agents.rag.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.configs.RetrieveStepConfig import RetrieveStepConfig
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
    SelfHostedEmbeddingParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_lib.testing.logging.logger import enable_logging
from aihub_lib.testing.milvus_vector_store_content import fill_collection, drop_collection

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig(
            agent_id="rag_agent",
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
            system_prompt=LocaleString(
                en="You're an agent answering user requests. Only use the context information provided."
            ),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2024-08-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=SelfHostedEmbeddingConfig(
                    name="Alibaba-NLP/gte-base-en-v1.5",
                    base_url="http://localhost:8183",
                    api_key=None,
                    timeout=60,
                    embed_batch_size=32,
                    default_parameter=SelfHostedEmbeddingParameter(
                        text_instruction=None,
                        query_instruction=None,
                        truncate_text=False,
                    ),
                ),
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode=VectorStoreQueryMode.DEFAULT,
                node_types=["content"],
                vector_store=create_milvus_vector_store(
                    uri="http://localhost",
                    collection_name="development",
                    embedding_vector_dimension=768,
                ),
            ),
            number_of_input_tokens=100000,
            condense_question_prompt=LocaleString(
                en="Given the following conversation between a user and an AI assistant and a follow-up question from the user,"
                "rephrase the follow-up question to be a standalone question."
                "\n"
                "Chat history:"
                "{chat_history}"
                "Follow-up input: {question}"
                "Standalone question:"
            ),
            context_prompt=LocaleString(
                en="You are provided with some additional context information in form of structured documents with its general"
                "structure and relevant information in more detail. Each document starts with an indicator <REFERENCE_DOCUMENT [metadata]>"
                "and ends with </REFERENCE_DOCUMENT>."
                "Here are the relevant documents for the context:"
                "\n"
                "{context_str}"
                "\n"
                "Instruction: Based on the above documents, provide a detailed answer for the user question below."
            ),
            check_context_sufficiency=True,
            max_hops=3,
        ),
    )

    fill_collection(
        runner.agent_config.retrieve_step_config.embed_model,
        runner.agent_config.retrieve_step_config.vector_store,
    )

    async with runner.test_run(delay_before_stop=60) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[
                    ChatMessage(
                        content="You're an agent answering user requests. Only use the context information provided.",
                        role=MessageRole.SYSTEM,
                    ),
                    ChatMessage(content="Hey. What is AI?", role=MessageRole.USER),
                ],
                user=fake_user(),
                locale="en",
            ),
        )

    drop_collection()


if __name__ == "__main__":
    asyncio.run(main())
