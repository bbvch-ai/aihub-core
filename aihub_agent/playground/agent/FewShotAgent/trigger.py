import asyncio

from aihub_lib.generative_ai.prompting.few_shot.FewShotExample import FewShotExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import StartEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.FewShotAgent import FewShotAgent, FewShotAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_agent.steps.prompting.few_shot_step.FewShotStepConfig import FewShotStepConfig

enable_logging()


async def main():
    runner = AgentTestRunner(
        default_agent_config=FewShotAgentConfig(
            agent_id="few_shot_agent",
            agent_class=FewShotAgent.__name__,
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent can transfer movie titles into emojis"),
            llm=LLMConfig(model_name="text-generation/mini"),
            number_of_input_tokens=100000,
            condense_question_prompt=LocaleString(en="""return the last user message"""),
            few_shot=FewShotStepConfig(
                few_shot_examples=[
                    FewShotExample(
                        user=LocaleString(en="James Bond"),
                        agent=LocaleString(en="🤵🍸🔫"),
                    ),
                    FewShotExample(
                        user=LocaleString(en="Harry Potter"),
                        agent=LocaleString(en="👓⚡️🪄"),
                    ),
                    FewShotExample(
                        user=LocaleString(en="Thor"),
                        agent=LocaleString(en="⚡️🧔‍♂️🔨"),
                    ),
                ],
                few_shot_system_prompt=LocaleString(en="Respond to the give movie title with three emojis"),
            ),
        ),
    )

    async with runner.test_run(delay_before_stop=60) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(
                locale="en",
                messages=[
                    ChatMessage(
                        content="You're an agent answering user requests. Only use the context information provided.",
                        role=MessageRole.SYSTEM,
                    ),
                    ChatMessage(content="Fight Club", role=MessageRole.USER),
                ],
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
