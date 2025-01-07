from typing import List

from aihub_agent.agents.AgentConfig import StepConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotExample import FewShotExample
from aihub_lib.i18n.LocaleString import LocaleString


class FewShotStepConfig(StepConfig):
    few_shot_examples: List[FewShotExample]
    few_shot_system_prompt: LocaleString | None
