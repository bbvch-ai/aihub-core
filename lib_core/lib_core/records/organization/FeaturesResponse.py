from pydantic import BaseModel, Field
from pydantic._internal._model_construction import ModelMetaclass

from lib_core.constants.features import FeatureFlag


class FeaturesResponseCheckMeta(ModelMetaclass):
    """Metaclass to check that all fields are present and no unexpected fields are present.
    With this metaclass, the class FeaturesResponse is forced to have all fields present in the enum FeatureFlag.
    Like this, we can ensure that when accessing FeatureFlags though the Enum that the flags are also respected in the
    FeaturesResponse object that is passed to the Frontend"""

    def __new__(mcs, name, bases, attrs):
        for feature in FeatureFlag:
            if feature.value not in attrs:
                raise TypeError(f"Missing field for feature: {feature.value}")
        for attr in attrs:
            if attr not in [feature.value for feature in FeatureFlag] and not attr.startswith("_"):
                raise TypeError(f"Unexpected field: {attr}")
        return super().__new__(mcs, name, bases, attrs)


class FeaturesResponse(BaseModel, metaclass=FeaturesResponseCheckMeta):
    prompt_enhance: bool = Field(
        ...,
        description="Flag whether the feature to enhance prompts is enabled.",
        example=False,
    )
    prompt_library: bool = Field(
        ...,
        description="Flag whether the feature to list globally preset prompts is enabled.",
        example=False,
    )
    voice_input: bool = Field(
        ...,
        description="Flag whether the feature to allow voice input is enabled.",
        example=False,
    )
    voice_output: bool = Field(
        ...,
        description="Flag whether the feature to allow voice output is enabled.",
        example=False,
    )
    tracing: bool = Field(
        ...,
        description="Flag whether the feature to trace agents behaviour is enabled.",
        example=False,
    )
    trace_user: bool = Field(
        ...,
        description="Flag whether the feature to trace user information when tracing is enabled. If tracing is "
        "disabled, this feature is ignored.",
        example=False,
    )
    usage_limits: bool = Field(
        ...,
        description="Flag whether the feature to display the usage limits is enabled.",
        example=False,
    )
    chat_export_import: bool = Field(
        ...,
        description="Flag whether the feature to allow export and imports of chats is enabled.",
        example=False,
    )
    save_questions: bool = Field(
        ...,
        description="Flag whether the feature to save the questions of the user is enabled.",
        example=False,
    )
    save_chat_history: bool = Field(
        ...,
        description="Flag whether the feature to save the chat history is enabled.",
        example=False,
    )
