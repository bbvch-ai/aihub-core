from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import StepConfig
from swiss_ai_hub.core.form import LocaleInput
from swiss_ai_hub.core.generative_ai import FewShotExample
from swiss_ai_hub.core.i18n import LocaleString


class FewShotStepConfig(StepConfig):
    """
    Configuration for few-shot prompting.
    """

    few_shot_examples: Annotated[
        list[FewShotExample],
        Field(description="List of few-shot examples to guide the agent's responses.", title="Few-Shot Examples"),
    ] = []
    system_prompt: Annotated[
        LocaleString | LocaleInput,
        Field(description="System prompt that sets the context for few-shot learning."),
    ]

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
