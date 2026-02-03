from typing import Annotated, Self

from aihub_lib.agents.AgentConfig import StepConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotExample import FewShotExample
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput
from pydantic import Field


class FewShotStepConfig(StepConfig):
    """
    Configuration for few-shot prompting.
    """

    few_shot_examples: Annotated[
        list[FewShotExample],
        Field(description="List of few-shot examples to guide the agent's responses.", title="Few-Shot Examples"),
    ] = []
    system_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="System prompt that sets the context for few-shot learning."),
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode FewShotStepConfig."""
        return cls(
            few_shot_examples=[FewShotExample.as_form()],
            system_prompt=LocaleInput(
                label=LocaleString(
                    en="System Prompt",
                    de="Systemaufforderung",
                    fr="Invite système",
                    it="Prompt di sistema",
                ),
                help=LocaleString(
                    en="Instructions for the agent when using few-shot examples",
                    de="Anweisungen für den Agenten bei der Verwendung von Few-Shot-Beispielen",
                    fr="Instructions pour l'agent lors de l'utilisation d'exemples few-shot",
                    it="Istruzioni per l'agente quando si utilizzano esempi few-shot",
                ),
                input_type="textarea",
                rows=3,
            ),
        )
