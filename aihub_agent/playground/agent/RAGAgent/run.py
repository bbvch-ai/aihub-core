import asyncio

from aihub_agent.agents.rag.Configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.RAGAgent import RAGAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.llms.models.embedding.azure.AzureOpenAIEmbeddingConfig import AzureOpenAIEmbeddingConfig, \
    AzureOpenAIEmbeddingParameter
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

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
                api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2023-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=AzureOpenAIEmbeddingConfig(
                    name="text-embedding-ada-002",
                    api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2023-12-01-preview",
                    embedding_tokens_costs_per_thousand=0.0,
                    default_parameter=AzureOpenAIEmbeddingParameter(),
                ),
                index_name="development",
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode="hybrid",
                node_types=["content"],
            ),
            number_of_input_tokens=2048,
            tokenizer_for_model="gpt-4o",
            condense_question_prompt=LocaleString(
                en="""
                    Given the following conversation between a user and an AI assistant and a follow-up question from the user,
                    rephrase the follow-up question to be a standalone question.

                    Chat history:
                    {chat_history}
                    Follow-up input: {question}
                    Standalone question:"""
            ),
            context_prompt=LocaleString(
                en="""
                    You are provided with some additional context information in form of structured documents with it's general
                    structure and relevant information in more detail. Each document starts with an indicator <DOC_START [documentname]>
                    and ends with <DOC_END [documentname]>.
                    Here are the relevant documents for the context:

                    {context_str}

                    Instruction: Based on the above documents, provide a detailed answer for the user question below."""
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
