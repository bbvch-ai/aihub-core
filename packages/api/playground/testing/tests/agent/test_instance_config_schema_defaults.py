"""Regression tests for aihub-core-private#335 — a checkbox ticking itself on profiles saved before the field existed.

`restrict_to_user_access` defaults to False on the model but seeds True on the form. The edit form fills a missing key
from the form value, so an old profile showed the box ticked while the agent ran unrestricted, and any save stored True.
The API now fills such keys with the schema default, which is what the agent applies at runtime.
"""

from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.form import Checkbox

from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper


class _RestrictableConfig(AgentConfig):
    restrict_to_user_access: Annotated[bool | Checkbox, Field(description="Restrict retrieval.")] = False

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            restrict_to_user_access=Checkbox(label="Restrict", value=True),
        )


def _schema() -> dict:
    return _RestrictableConfig.as_form().to_configurable_submission_model().model_json_schema()


def test_missing_key_takes_the_runtime_default_not_the_form_value() -> None:
    config = InstanceConfigHelper.with_schema_defaults({"agent_id": "old-profile"}, _schema())

    assert config["restrict_to_user_access"] is False


def test_stored_values_win_over_the_schema_default() -> None:
    schema = _schema()

    assert InstanceConfigHelper.with_schema_defaults({"restrict_to_user_access": True}, schema)[
        "restrict_to_user_access"
    ]
    assert not InstanceConfigHelper.with_schema_defaults({"restrict_to_user_access": False}, schema)[
        "restrict_to_user_access"
    ]


def test_null_nested_and_list_defaults_are_left_to_the_frontend() -> None:
    schema = {
        "properties": {
            "reranking_config": {"default": None},
            "memory": {"default": {"enabled": True}},
            "examples": {"default": []},
            "required_field": {"type": "string"},
            "retrieve_k": {"default": 5},
        }
    }

    assert InstanceConfigHelper.with_schema_defaults({}, schema) == {"retrieve_k": 5}


def test_missing_schema_leaves_the_config_untouched() -> None:
    assert InstanceConfigHelper.with_schema_defaults({"agent_id": "a"}, {}) == {"agent_id": "a"}
