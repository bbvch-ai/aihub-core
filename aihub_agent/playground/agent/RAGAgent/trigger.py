import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.core.vector_stores.types import VectorStoreQueryMode

from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
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
from aihub_lib.persistence.rag.vectors.node_metadata import (
    DOCUMENT_TITLE,
    NAMESPACE,
    NODE_TYPE_CONTENT,
    SOURCE,
    TYPE,
    HEADING_LEVEL,
    SECTION_START_LINE,
    INDEX,
    NODE_TYPE_SUMMARY,
    H1,
    H2,
)
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
                name="gpt-4o-mini",
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
                retrieve_k=2,
                query_mode=VectorStoreQueryMode.DEFAULT,
                node_types=["content"],
                vector_store=create_milvus_vector_store(
                    uri="http://localhost",
                    collection_name="test_rag_relations_123456",
                    embedding_vector_dimension=768,
                ),
                retrieve_prev_next=RetrievePrevNextConfig(num_nodes=1, mode=ModeOptions.BOTH),
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
            check_context_sufficiency=True,
            max_hops=3,
        ),
    )

    def create_test_nodes_with_relationships():
        node1 = TextNode(
            text="# Artifcial Insanity\nAI is crazy. It stands for artificial insanity.",
            metadata={
                DOCUMENT_TITLE: "Document 1",
                SOURCE: "ai_knowledge",
                NAMESPACE: "ai_knowledge",
                TYPE: NODE_TYPE_CONTENT,
                HEADING_LEVEL: 1,
                SECTION_START_LINE: 0,
                INDEX: 0,
                H1: "Artifcial Insanity",
            },
        )
        summary_h1 = TextNode(
            text="AI stands for artificial insanity, artifical ignorance and aritfical imaginaton.",
            metadata={
                DOCUMENT_TITLE: "Document 1",
                SOURCE: "ai_knowledge",
                NAMESPACE: "ai_knowledge",
                TYPE: NODE_TYPE_SUMMARY,
                HEADING_LEVEL: 1,
                SECTION_START_LINE: 0,
                INDEX: 0,
                H1: "Artifcial Insanity",
            },
        )
        node2 = TextNode(
            text="## Aritifical Ignorance\nAI is terrible. It stands for artificial ignorance.",
            metadata={
                DOCUMENT_TITLE: "Document 1",
                SOURCE: "ai_knowledge",
                NAMESPACE: "ai_knowledge",
                TYPE: NODE_TYPE_CONTENT,
                HEADING_LEVEL: 2,
                SECTION_START_LINE: 1,
                INDEX: 1,
                H1: "Artifcial Insanity",
                H2: "Aritifical Ignorance",
            },
        )
        summary_h2 = TextNode(
            text="AI stands for artificial ignorance and is terrible.",
            metadata={
                DOCUMENT_TITLE: "Document 1",
                SOURCE: "ai_knowledge",
                NAMESPACE: "ai_knowledge",
                TYPE: NODE_TYPE_SUMMARY,
                HEADING_LEVEL: 2,
                SECTION_START_LINE: 1,
                INDEX: 1,
                H1: "Artifcial Insanity",
                H2: "Aritifical Ignorance",
            },
        )
        node3 = TextNode(
            text="##Artifical Imagination\nAI is amazing. It stands for artificial imagination.",
            metadata={
                DOCUMENT_TITLE: "Document 1",
                SOURCE: "ai_knowledge",
                NAMESPACE: "ai_knowledge",
                TYPE: NODE_TYPE_CONTENT,
                HEADING_LEVEL: 3,
                SECTION_START_LINE: 2,
                INDEX: 2,
                H1: "Artifcial Insanity",
                H2: "Aritifical Imagination",
            },
        )
        summary_h3 = TextNode(
            text="AI stands for artificial imagination and is amazing.",
            metadata={
                DOCUMENT_TITLE: "Document 1",
                SOURCE: "ai_knowledge",
                NAMESPACE: "ai_knowledge",
                TYPE: NODE_TYPE_SUMMARY,
                HEADING_LEVEL: 3,
                SECTION_START_LINE: 2,
                INDEX: 2,
                H1: "Artifcial Insanity",
                H2: "Aritifical Imagination",
            },
        )

        # Set up relationships
        node1.relationships = {
            NodeRelationship.PARENT: RelatedNodeInfo(node_id=summary_h1.node_id),
        }
        node2.relationships = {
            NodeRelationship.PARENT: RelatedNodeInfo(node_id=summary_h2.node_id),
            NodeRelationship.PREVIOUS: RelatedNodeInfo(node_id=node1.node_id),
        }
        node3.relationships = {
            NodeRelationship.PARENT: RelatedNodeInfo(node_id=summary_h3.node_id),
            NodeRelationship.PREVIOUS: RelatedNodeInfo(node_id=node1.node_id),
        }
        summary_h1.relationships = {
            NodeRelationship.CHILD: [
                RelatedNodeInfo(node_id=node1.node_id),
                RelatedNodeInfo(node_id=summary_h2.node_id),
                RelatedNodeInfo(node_id=summary_h3.node_id),
            ],
        }
        summary_h2.relationships = {
            NodeRelationship.CHILD: [RelatedNodeInfo(node_id="node2")],
            NodeRelationship.PARENT: RelatedNodeInfo(node_id="summary_h1"),
        }
        summary_h3.relationships = {
            NodeRelationship.CHILD: [RelatedNodeInfo(node_id="node3")],
            NodeRelationship.PARENT: RelatedNodeInfo(node_id="summary_h1"),
        }

        return [node1, node2, node3, summary_h1, summary_h2, summary_h3]

    # Create the test nodes
    TEST_NODES = create_test_nodes_with_relationships()
    fill_collection(
        runner.agent_config.retrieve_step_config.embed_model,
        runner.agent_config.retrieve_step_config.vector_store,
        nodes=TEST_NODES,
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

    drop_collection(collection_name="test_rag_relations_123456")


if __name__ == "__main__":
    asyncio.run(main())
