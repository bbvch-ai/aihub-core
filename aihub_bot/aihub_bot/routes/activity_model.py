from datetime import datetime
from typing import Any, Dict, List, Type

from botbuilder.schema import ChannelAccount, ConversationAccount, MessageReaction, SuggestedActions, \
    Attachment, ConversationReference, TextHighlight, SemanticAction, Activity
from msrest.serialization import Model
from pydantic import create_model


def _type_to_pydantic(str_type: Type[Model]) -> Any:
    if str_type._attribute_map:
        fields = {}
        for info in str_type._attribute_map.values():
            fields[info["key"]] = (_string_to_type(info["type"]), None)
        return create_model(str_type.__name__, **fields)


def _string_to_type(type_str: str) -> Any:
    """
    Convert a string representation of a type (as specified in the _attribute_map)
    into an actual Python type.
    """
    # Handle simple types.
    if type_str == "str":
        return str
    if type_str == "bool":
        return bool
    if type_str == "object":
        return dict
    if type_str == "iso-8601":
        return datetime

    # Handle list types (e.g. "[ChannelAccount]").
    if type_str.startswith("[") and type_str.endswith("]"):
        inner_type_str = type_str[1:-1].strip()  # Remove the surrounding brackets.
        inner_type = _string_to_type(inner_type_str)
        return List[inner_type]

    # Handle map types (e.g. "{ChannelAccount}").
    if type_str.startswith("{") and type_str.endswith("}"):
        inner_type_str = type_str[1:-1].strip()
        inner_type = _string_to_type(inner_type_str)
        return Dict[str, inner_type]

    # Map custom types. Add or modify entries based on your actual types.
    custom_types: Dict[str, Type[Model]] = {
        "ChannelAccount": ChannelAccount,
        "ConversationAccount": ConversationAccount,
        "MessageReaction": MessageReaction,
        "SuggestedActions": SuggestedActions,
        "Attachment": Attachment,
        "ConversationReference": ConversationReference,
        "TextHighlight": TextHighlight,
        "SemanticAction": SemanticAction,
    }

    if type_str in custom_types:
        return _type_to_pydantic(custom_types[type_str])

    return Any


ActivityModel = _type_to_pydantic(Activity)
