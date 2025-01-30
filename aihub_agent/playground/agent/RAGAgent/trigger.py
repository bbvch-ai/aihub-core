import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.rag.Configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.RAGAgent import RAGAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.llms.models.chat.self_hosted.SelfHostedLLMConfig import (
    SelfHostedLLMConfig,
    SelfHostedLLMParameter,
)
from aihub_lib.generative_ai.llms.models.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
    SelfHostedEmbeddingParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.testing.logging.logger import enable_logging
from playground.agent.RAGAgent.milvus_vector_store_content import fill_collection, drop_collection

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
            llm=SelfHostedLLMConfig(
                name="unsloth/Llama-3.2-1B-Instruct",
                base_url="http://localhost:8182/v1",
                api_key=None,
                context_size=512,
                is_chat_model=True,
                is_function_calling_model=False,
                default_parameter=SelfHostedLLMParameter(
                    logit_bias=None,
                    logprobs=None,
                ),
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
                "structure and relevant information in more detail. Each document starts with an indicator <DOC_START [documentname]>"
                "and ends with <DOC_END [documentname]>."
                "Here are the relevant documents for the context:"
                "\n"
                "{context_str}"
                "\n"
                "Instruction: Based on the above documents, provide a detailed answer for the user question below."
            ),
        ),
    )

    fill_collection(
        runner.agent_config.retrieve_step_config.embed_model,
        runner.agent_config.retrieve_step_config.vector_store,
    )

    async with runner.test_run(delay_before_stop=60) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(
                messages=[
                    ChatMessage(
                        content="You're an agent answering user requests. Only use the context information provided.",
                        role=MessageRole.SYSTEM,
                    ),
                    ChatMessage(content="Hey! What is AI?", role=MessageRole.USER),
                ]
            ),
        )

    drop_collection()


if __name__ == "__main__":
    asyncio.run(main())
