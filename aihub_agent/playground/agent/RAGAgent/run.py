import asyncio

from dotenv import load_dotenv
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.testing.logging.logger import enable_logging

enable_logging(30)
load_dotenv()


async def main():
    runner = AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig(
            agent_id="dev_agent",
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
            system_prompt=LocaleString(
                en="You're an agent answering user requests. Only use the context information provided, either as documents or images."
                "Analyze the context information and provide a detailed answer to the user question. If you don't know the answer, say 'I don't know'."
            ),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url="https://bbvaihub-openai-sui.openai.azure.com",
                api_version="2025-01-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=AzureOpenAIEmbeddingConfig(
                    name="text-embedding-3-large",
                    base_url="https://bbvaihub-openai-sui.openai.azure.com",
                    api_version="2024-12-01-preview",
                    embedding_tokens_costs_per_thousand=0.0,
                ),
                index_namespaces=["test"],
                retrieve_k=5,
                query_mode=VectorStoreQueryMode.DEFAULT,
                node_types=["content"],
                vector_store=create_milvus_vector_store(
                    uri="http://localhost:19530",
                    collection_name="test",
                    embedding_vector_dimension=3072,
                ),
                retrieve_prev_next=RetrievePrevNextConfig(num_nodes=10, mode=ModeOptions.BOTH),
            ),
            number_of_input_tokens=100_000,
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
                "and ends with </REFERENCE_DOCUMENT>. Inside the documents images are marked with <IMAGE> tags. Take a look ath the images"
                "if there are any, they might contain relevant information for the user question."
                "Here are the relevant documents for the context:"
                "\n"
                "{context_str}"
                "\n"
                "Instruction: Based on the above documents, provide a detailed answer for the user question below."
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

{
    "number_of_pages": 11,
    "namespace": "test_ksb",
    "content_hash": "NJ8WwYT7BNPJBcyDOyGqmw==",
    "updated_at": 1749201967,
    "created_at": 1749203801,
    "inserted_at": 1749203801,
    "type": "content",
    "data_lake_uri": "playground/test_ksb/6.36 Aufzug/6.36 Aufzug/Checkliste für Gebäudekontrolle vor Montagebeginn.pdf",
    "source": "playground/test_ksb/6.36 Aufzug/6.36 Aufzug/Checkliste für Gebäudekontrolle vor Montagebeginn.pdf",
    "document_title": "Checkliste für Gebäudekontrolle vor Montagebeginn.pdf",
    "language": "en",
    "version": 1,
    "index": 13,
    "page": 2,
    "section_start_line": 51,
    "section_end_line": 293,
    "h1": "2.1",
    "h2": null,
    "h3": null,
    "h4": null,
    "h5": null,
    "h6": null,
    "heading_level": 1,
    "reference_name": null,
    "reference_url": null,
    "_node_content": '{"id_": "09f8f46b-8662-42ee-8d08-4693f3188041", "embedding": null, "metadata": {"number_of_pages": 11, "namespace": "test_ksb", "content_hash": "NJ8WwYT7BNPJBcyDOyGqmw==", "updated_at": 1749201967, "created_at": 1749203801, "inserted_at": 1749203801, "type": "content", "data_lake_uri": "playground/test_ksb/6.36 Aufzug/6.36 Aufzug/Checkliste f\\u00fcr Geb\\u00e4udekontrolle vor Montagebeginn.pdf", "source": "playground/test_ksb/6.36 Aufzug/6.36 Aufzug/Checkliste f\\u00fcr Geb\\u00e4udekontrolle vor Montagebeginn.pdf", "document_title": "Checkliste f\\u00fcr Geb\\u00e4udekontrolle vor Montagebeginn.pdf", "language": "en", "version": 1, "index": 13, "page": 2, "section_start_line": 51, "section_end_line": 293, "h1": "2.1", "h2": null, "h3": null, "h4": null, "h5": null, "h6": null, "heading_level": 1, "reference_name": null, "reference_url": null}, "excluded_embed_metadata_keys": [], "excluded_llm_metadata_keys": [], "relationships": {"1": {"node_id": "aa47a5053c83b81cd85fe680", "node_type": "4", "metadata": {"number_of_pages": 11, "namespace": "test_ksb", "content_hash": "NJ8WwYT7BNPJBcyDOyGqmw==", "updated_at": 1749201967, "created_at": 1749203801, "inserted_at": 1749203801, "type": "content", "data_lake_uri": "playground/test_ksb/6.36 Aufzug/6.36 Aufzug/Checkliste f\\u00fcr Geb\\u00e4udekontrolle vor Montagebeginn.pdf", "source": "playground/test_ksb/6.36 Aufzug/6.36 Aufzug/Checkliste f\\u00fcr Geb\\u00e4udekontrolle vor Montagebeginn.pdf", "document_title": "Checkliste f\\u00fcr Geb\\u00e4udekontrolle vor Montagebeginn.pdf"}, "hash": "NJ8WwYT7BNPJBcyDOyGqmw==", "class_name": "RelatedNodeInfo"}, "2": {"node_id": "9d041429-582d-48e6-b709-43e774fdf59a", "node_type": null, "metadata": {}, "hash": null, "class_name": "RelatedNodeInfo"}, "3": {"node_id": "510f3c4e-0ffc-4ac9-8b21-2264ac2366d0", "node_type": null, "metadata": {}, "hash": null, "class_name": "RelatedNodeInfo"}, "4": {"node_id": "dd5030e1-467b-4152-9add-f6a7be15aaa2", "node_type": null, "metadata": {}, "hash": null, "class_name": "RelatedNodeInfo"}}, "metadata_template": "{key}: {value}", "metadata_separator": "\\n", "text": "", "mimetype": "text/plain", "start_char_idx": 745, "end_char_idx": 754, "metadata_seperator": "\\n", "text_template": "{metadata_str}\\n\\n{content}", "class_name": "TextNode"}',
    "_node_type": "TextNode",
    "doc_id": "aa47a5053c83b81cd85fe680",
    "ref_doc_id": "aa47a5053c83b81cd85fe680",
}
