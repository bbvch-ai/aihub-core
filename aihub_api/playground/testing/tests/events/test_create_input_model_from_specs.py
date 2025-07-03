from typing import Type

import pytest
from pydantic import BaseModel

from aihub_api.events.create_input_model import create_input_model_from_specs
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from playground.testing.tests.events.TestEvent import TestEvent, NestedTestModel


@pytest.fixture
def event_specs() -> EventSpecs:
    return EventSpecs(event_name=TestEvent.event_name_from_class(), event_schema=TestEvent.model_json_schema())


@pytest.fixture
def pydantic_model(event_specs) -> Type[BaseModel]:
    return create_input_model_from_specs(event_specs)


@pytest.fixture
def pydantic_instance(pydantic_model) -> BaseModel:
    return pydantic_model(
        test_field="test_value", nested_model={"nested_field": "nested_value", "nested_optional": 123}
    )


@pytest.fixture
def pydantic_instance_minimal(pydantic_model) -> BaseModel:
    return pydantic_model(test_field="test_value", nested_model={"nested_field": "nested_value"})


class TestCreateInputModel:
    def test_model_creation(self, pydantic_model):
        assert pydantic_model is not None

    def test_model_name(self, pydantic_model):
        assert pydantic_model.__name__ == f"{TestEvent.event_name_from_class()}Input"

    def test_model_excluded_fields(self, pydantic_model):
        assert "event_id" not in pydantic_model.model_fields
        assert "created_at" not in pydantic_model.model_fields

    def test_model_included_fields(self, pydantic_model):
        assert "test_field" in pydantic_model.model_fields
        assert "test_field_with_default" in pydantic_model.model_fields
        assert "nested_model" in pydantic_model.model_fields
        assert "optional_nested" in pydantic_model.model_fields

    def test_instance_creation(self, pydantic_instance):
        assert isinstance(pydantic_instance, BaseModel)
        assert pydantic_instance.test_field == "test_value"
        assert pydantic_instance.test_field_with_default == 42
        assert pydantic_instance.nested_model.nested_field == "nested_value"
        assert pydantic_instance.nested_model.nested_optional == 123
        assert pydantic_instance.optional_nested is None

    def test_nested_model_validation(self, pydantic_instance_minimal):
        assert pydantic_instance_minimal.nested_model.nested_field == "nested_value"
        assert pydantic_instance_minimal.nested_model.nested_optional is None

    def test_nested_model_field_type(self, pydantic_model):
        nested_field = pydantic_model.model_fields["nested_model"]
        assert isinstance(nested_field.annotation, type)
        assert issubclass(nested_field.annotation, BaseModel)

    def test_nested_model_schema_validation(self, event_specs):
        schema = event_specs.event_schema
        nested_model_prop = schema["properties"]["nested_model"]
        assert "$ref" in nested_model_prop
        assert nested_model_prop["$ref"] == "#/$defs/NestedTestModel"

        nested_def = schema["$defs"]["NestedTestModel"]
        assert nested_def["type"] == "object"
        assert "nested_field" in nested_def["properties"]
        assert "nested_optional" in nested_def["properties"]
