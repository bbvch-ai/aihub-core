import asyncio

from aihub_lib.generative_ai.prompting.few_shot.FewShotExample import FewShotExample
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

from aihub_agent.agents.FewShotAgent import FewShotAgent
from aihub_agent.agents.FewShotAgent.FewShowAgentConfig import FewShotAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_agent.steps.prompting.few_shot_step.FewShotStepConfig import FewShotStepConfig

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=FewShotAgent,
        agent_config=FewShotAgentConfig(
            agent_id="rag_agent",
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
            system_prompt=LocaleString(
                en="You're an agent answering user requests. Only use the context information provided."
            ),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2024-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
            number_of_input_tokens=100000,
            condense_question_prompt=LocaleString(
                en="""
                    Given the following conversation between a user and an AI assistant and 
                    a follow-up question from the user,
                    rephrase the follow-up question to be a standalone question.

                    Chat history:
                    {chat_history}
                    Follow-up input: {question}
                    Standalone question:"""
            ),
            few_shot=FewShotStepConfig(
                few_shot_examples=[
                    FewShotExample(
                        user=LocaleString(en="1"),
                        agent=LocaleString(en="2"),
                    ),
                    FewShotExample(
                        user=LocaleString(en="four"),
                        agent=LocaleString(en="five"),
                    ),
                    FewShotExample(
                        user=LocaleString(en="fünf"),
                        agent=LocaleString(en="sechs"),
                    ),
                ],
                few_shot_system_prompt=LocaleString(en="Add one to the given Number"),
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
