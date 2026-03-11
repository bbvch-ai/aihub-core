from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.PrimeVueElement import PrimeVueElement
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class ModelSelect(PrimeVueElement):
    """
    A FormKit element for selecting LLM models from LiteLLM.

    This element renders as a select dropdown that automatically fetches
    available models from the API based on the specified mode.

    The frontend component handles fetching models from `/api/v1/models/mode/{mode}`
    and populating the dropdown options.

    ### Supported Modes
    - `chat`: Chat/text generation models
    - `embedding`: Embedding models
    - `rerank`: Reranking models
    - `image_generation`: Image generation models
    - `audio_transcription`: Audio transcription models
    - `audio_speech`: Text-to-speech models

    ### Example Usage
    ```python
    class MyAgentConfig(AgentConfig):
        llm_model: Annotated[
            str | ModelSelect,
            Field(description="The LLM model to use"),
        ]

    # Form mode - for rendering:
    config = MyAgentConfig(
        llm_model=ModelSelect(
            label=LocaleString(en="Model", de="Modell"),
            mode="chat",
        ),
    )

    # Data mode - from submission:
    config = MyAgentConfig(
        llm_model="text-generation/gpt-4",
    )
    ```
    """

    formkit: Annotated[Literal["modelSelect"], Field(description="Model select element.")] = "modelSelect"

    mode: Annotated[
        Literal["chat", "embedding", "rerank", "image_generation", "audio_transcription", "audio_speech"],
        Field(description="The model mode to fetch options for."),
    ] = "chat"

    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    filter: Annotated[bool, Field(description="Whether to enable filtering/search")] = True
    show_clear: Annotated[bool, Field(description="Whether to show clear button", alias="showClear")] = False

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy
