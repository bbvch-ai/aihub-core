"""Helper functions for creating common form element patterns."""

from typing import Literal

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.elements.Select import Select
from aihub_lib.nats.events.form.elements.Textarea import Textarea


def create_locale_string_group(
    name: str,
    label: LocaleString,
    input_type: Literal["text", "textarea"] = "text",
    rows: int = 3,
    help_text: LocaleString | None = None,
) -> Group:
    """
    Creates a Group containing four language fields (en, de, fr, it) for LocaleString input.

    This is the standard pattern for multi-language text fields in the AI-Hub platform.
    Each language gets its own input field within a labeled group.

    Args:
        name: The form field name (becomes key in submitted data, e.g., "name", "description")
        label: The group label displayed above the fields in all four languages
        input_type: "text" for single-line InputText, "textarea" for multi-line Textarea
        rows: Number of rows for textarea (only used when input_type="textarea")
        help_text: Optional help text template shown below each language field
    """
    languages = [
        ("en", LocaleString(en="English", de="Englisch", fr="Anglais", it="Inglese")),
        ("de", LocaleString(en="German", de="Deutsch", fr="Allemand", it="Tedesco")),
        ("fr", LocaleString(en="French", de="Französisch", fr="Français", it="Francese")),
        ("it", LocaleString(en="Italian", de="Italienisch", fr="Italien", it="Italiano")),
    ]

    children: list[InputText | Textarea] = []
    for lang_code, lang_label in languages:
        if input_type == "textarea":
            element: InputText | Textarea = Textarea(
                name=lang_code,
                label=lang_label,
                help=help_text.model_copy() if help_text else None,
                rows=rows,
                auto_resize=True,
            )
        else:
            element = InputText(
                name=lang_code,
                label=lang_label,
                help=help_text.model_copy() if help_text else None,
            )
        children.append(element)

    return Group(name=name, label=label, children=children)


def create_model_select_field(
    name: str,
    label: LocaleString,
    options_api_mode: Literal["chat", "embedding", "rerank", "image_generation", "audio_transcription", "audio_speech"],
    help_text: LocaleString | None = None,
) -> Select:
    """
    Creates a Select field that fetches model options from the API.

    The options_api_mode determines which type of models are fetched from the LiteLLM gateway.

    Args:
        name: The form field name (e.g., "model_name")
        label: The field label in all four languages
        options_api_mode: The API mode for fetching available models:
            - "chat": Chat/completion models (GPT-4, Claude, etc.)
            - "embedding": Embedding models (text-embedding-ada, etc.)
            - "rerank": Reranking models (Cohere, etc.)
            - "image_generation": Image generation models
            - "audio_transcription": Speech-to-text models
            - "audio_speech": Text-to-speech models
        help_text: Optional help text shown below the field
    """
    return Select(
        name=name,
        label=label,
        help=help_text,
        options_api_mode=options_api_mode,
    )
