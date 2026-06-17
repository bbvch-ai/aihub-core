from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.agent.agents.rag_agent.rag_agent import (
    follow_up_suggestion_enabled,
    tag_generation_enabled,
    title_generation_enabled,
)
from swiss_ai_hub.agent.steps.conversation_metadata.conversation_metadata_step_config import (
    ConversationMetadataStepConfig,
)


def _config(metadata: ConversationMetadataStepConfig) -> MagicMock:
    config = MagicMock()
    config.conversation_metadata = metadata
    return config


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("precondition", "field"),
    [
        (title_generation_enabled, "generate_title"),
        (tag_generation_enabled, "generate_tags"),
        (follow_up_suggestion_enabled, "suggest_follow_ups"),
    ],
)
async def test_precondition_follows_config_flag(precondition, field):
    enabled = _config(ConversationMetadataStepConfig(**{field: True}))
    disabled = _config(ConversationMetadataStepConfig(**{field: False}))

    assert await precondition(event=MagicMock(), config=enabled) is True
    assert await precondition(event=MagicMock(), config=disabled) is False
