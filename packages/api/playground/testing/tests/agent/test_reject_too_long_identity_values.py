"""Length limits on the identity fields an agent form announces, enforced at save time.

The form is round-tripped through the stored dict shape the API reads back, so the limits asserted here are the ones
that survive discovery and reach `reject_invalid_values`.
"""

from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import TypeAdapter
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, FormkitElement
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper


def _elements() -> list[FormkitElement]:
    stored = [element.model_dump(by_alias=True) for element in AgentConfig.as_form().to_formkit_form()]
    return TypeAdapter(list[ALL_FORM_OPTIONS]).validate_python(stored)


def _config(name: str = "Helper", description: str = "Answers questions", agent_id: str = "helper") -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "name": {"de": None, "en": name, "fr": None, "it": None},
        "description": {"de": None, "en": description, "fr": None, "it": None},
    }


def _reject(config: dict[str, Any]) -> None:
    InstanceConfigHelper.reject_invalid_values(_elements(), config, LocaleHandler(locale="en"))


def test_values_at_the_limits_are_accepted():
    _reject(
        _config(
            name="n" * AgentConfig.NAME_MAX_LENGTH,
            description="d" * AgentConfig.DESCRIPTION_MAX_LENGTH,
            agent_id="i" * AgentConfig.ID_MAX_LENGTH,
        )
    )


@pytest.mark.parametrize(
    ("config", "field", "limit"),
    [
        (_config(name="n" * (AgentConfig.NAME_MAX_LENGTH + 1)), "name", AgentConfig.NAME_MAX_LENGTH),
        (
            _config(description="d" * (AgentConfig.DESCRIPTION_MAX_LENGTH + 1)),
            "description",
            AgentConfig.DESCRIPTION_MAX_LENGTH,
        ),
    ],
)
def test_a_locale_value_over_the_limit_is_rejected(config: dict[str, Any], field: str, limit: int):
    with pytest.raises(HTTPException) as raised:
        _reject(config)

    assert raised.value.status_code == 400
    assert raised.value.detail == (
        f"Configuration validation failed: {field}: must be at most {limit} characters per language (en)"
    )


def test_an_agent_id_over_the_limit_is_rejected():
    with pytest.raises(HTTPException) as raised:
        _reject(_config(agent_id="i" * (AgentConfig.ID_MAX_LENGTH + 1)))

    assert raised.value.detail == (
        f"Configuration validation failed: agent_id: must be at most {AgentConfig.ID_MAX_LENGTH} characters"
    )
