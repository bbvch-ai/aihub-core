import asyncio
from os.path import abspath, join, dirname

from aihub_bot.routes.chat.agent.AgentChatController import AgentChatController
from aihub_bot.routes.chat.openai.OpenaiChatController import OpenaiChatController
from aihub_bot.routes.echo.EchoController import EchoController
from aihub_bot.runners.SimulatedAgentBotTestRunner import SimulatedAgentBotTestRunner
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig, \
    AzureOpenAIParameter
from aihub_lib.generative_ai.llms.models.chat.self_hosted.SelfHostedLLMConfig import SelfHostedLLMConfig, \
    SelfHostedLLMParameter
from aihub_lib.routes.health.HealthController import HealthController


async def main():
    runner = SimulatedAgentBotTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()

    runner.mount(
        HealthController().get_health(),
        AgentChatController().completions_json().completions_stream(),
        EchoController().post_messages(),
        OpenaiChatController(
            chat_models=[
                SelfHostedLLMConfig(
                    name="unsloth/Llama-3.2-1B-Instruct",
                    base_url="http://localhost:8182/v1",
                    is_function_calling_model=False,
                    context_size=512,
                    is_chat_model=True,
                    default_parameter=SelfHostedLLMParameter(
                        logit_bias=None,
                        logprobs=None,
                        temperature=0.0,
                        top_p=1.0,
                        max_tokens=None,
                        frequency_penalty=0.0,
                        presence_penalty=0.0,
                        seed=0,
                    ),
                    api_key=None,
                ),
                AzureOpenAILLMConfig(
                    name="gpt-4o",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-08-01-preview",
                    prompt_tokens_costs_per_thousand=0.0045,
                    completion_tokens_costs_per_thousand=0.0133,
                    default_parameter=AzureOpenAIParameter(
                        logit_bias=None,
                        logprobs=False,
                        temperature=0.0,
                        top_p=1.0,
                        max_tokens=None,
                        frequency_penalty=0.0,
                        presence_penalty=0.0,
                        seed=0,
                        top_logprobs=None,
                    ),
                ),
                AzureOpenAILLMConfig(
                    name="o1-mini",
                    base_url="https://aihub-dev-openai-swe-whisper.openai.azure.com",
                    api_version="2024-08-01-preview",
                    prompt_tokens_costs_per_thousand=0.0045,
                    completion_tokens_costs_per_thousand=0.0133,
                    default_parameter=AzureOpenAIParameter(
                        logit_bias=None,
                        logprobs=False,
                        temperature=0.0,
                        top_p=1.0,
                        max_tokens=None,
                        frequency_penalty=0.0,
                        presence_penalty=0.0,
                        seed=0,
                        top_logprobs=None,
                    ),
                ),
            ],
        )
        .json_chat_completion()
        .stream_chat_completion(),
    )

    runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
