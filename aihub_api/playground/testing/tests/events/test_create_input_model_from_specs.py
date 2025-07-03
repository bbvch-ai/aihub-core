from typing import Type

import pytest
from pydantic import BaseModel

from aihub_api.events.EventModelCreationService import EventModelCreationService
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from playground.testing.tests.events.TestEvent import TestEvent, NestedTestModel, Level2Model, Level3Model


@pytest.fixture
def event_specs() -> EventSpecs:
    return EventSpecs(event_name=TestEvent.event_name_from_class(), event_schema=TestEvent.model_json_schema())


@pytest.fixture
def pydantic_model(event_specs) -> Type[BaseModel]:
    return EventModelCreationService.create_input_model_from_specs(event_specs)


@pytest.fixture
def pydantic_instance(pydantic_model) -> BaseModel:
    return pydantic_model(
        test_field="test_value",
        nested_model={
            "nested_field": "nested_value",
            "nested_optional": 123,
            "level2": {"level2_data": "level2_value", "level3": {"deep_value": "deep_test", "deep_number": 777}},
        },
        union_field="string_value",
        complex_union="complex_string",
        list_of_nested=[{"nested_field": "item1"}, {"nested_field": "item2"}],
    )


@pytest.fixture
def pydantic_instance_minimal(pydantic_model) -> BaseModel:
    return pydantic_model(
        test_field="test_value",
        nested_model={"nested_field": "nested_value"},
        union_field=42,
        complex_union={"nested_field": "complex_nested"},
        list_of_nested=[],
    )


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
        assert "union_field" in pydantic_model.model_fields
        assert "complex_union" in pydantic_model.model_fields
        assert "list_of_nested" in pydantic_model.model_fields
        assert "optional_union" in pydantic_model.model_fields

    def test_instance_creation(self, pydantic_instance):
        assert isinstance(pydantic_instance, BaseModel)
        assert pydantic_instance.test_field == "test_value"
        assert pydantic_instance.test_field_with_default == 42
        assert pydantic_instance.nested_model.nested_field == "nested_value"
        assert pydantic_instance.nested_model.nested_optional == 123
        assert pydantic_instance.optional_nested is None

    def test_deep_nesting(self, pydantic_instance):
        # Test 3-level deep nesting
        assert pydantic_instance.nested_model.level2.level2_data == "level2_value"
        assert pydantic_instance.nested_model.level2.level3.deep_value == "deep_test"
        assert pydantic_instance.nested_model.level2.level3.deep_number == 777

    def test_union_types(self, pydantic_instance, pydantic_instance_minimal):
        # String union
        assert pydantic_instance.union_field == "string_value"
        # Integer union
        assert pydantic_instance_minimal.union_field == 42
        # Complex union with nested model
        assert pydantic_instance_minimal.complex_union.nested_field == "complex_nested"

    def test_list_of_nested(self, pydantic_instance):
        assert len(pydantic_instance.list_of_nested) == 2
        assert pydantic_instance.list_of_nested[0].nested_field == "item1"
        assert pydantic_instance.list_of_nested[1].nested_field == "item2"

    def test_nested_model_validation(self, pydantic_instance_minimal):
        assert pydantic_instance_minimal.nested_model.nested_field == "nested_value"
        assert pydantic_instance_minimal.nested_model.nested_optional is None

    def test_nested_model_field_type(self, pydantic_model):
        nested_field = pydantic_model.model_fields["nested_model"]
        # For JSON schema-based models with $ref, we get a dynamically created model
        assert isinstance(nested_field.annotation, type)
        assert issubclass(nested_field.annotation, BaseModel)

    def test_nested_model_schema_validation(self, event_specs):
        schema = event_specs.event_schema
        nested_model_prop = schema["properties"]["nested_model"]
        # Nested models use $ref instead of inline type
        assert "$ref" in nested_model_prop
        assert nested_model_prop["$ref"] == "#/$defs/NestedTestModel"

        # Check the actual nested model definition
        nested_def = schema["$defs"]["NestedTestModel"]
        assert nested_def["type"] == "object"
        assert "nested_field" in nested_def["properties"]
        assert "nested_optional" in nested_def["properties"]
        assert "level2" in nested_def["properties"]

    def test_deep_nesting_schema(self, event_specs):
        schema = event_specs.event_schema
        defs = schema["$defs"]

        # Check Level2Model definition
        level2_def = defs["Level2Model"]
        assert level2_def["type"] == "object"
        assert "level2_data" in level2_def["properties"]
        assert "level3" in level2_def["properties"]
        assert level2_def["properties"]["level3"]["$ref"] == "#/$defs/Level3Model"

        # Check Level3Model definition
        level3_def = defs["Level3Model"]
        assert level3_def["type"] == "object"
        assert "deep_value" in level3_def["properties"]
        assert "deep_number" in level3_def["properties"]

    def test_union_schema_validation(self, event_specs):
        schema = event_specs.event_schema
        union_field_prop = schema["properties"]["union_field"]

        # Union types should have anyOf
        assert "anyOf" in union_field_prop
        types = [item.get("type") for item in union_field_prop["anyOf"]]
        assert "string" in types
        assert "integer" in types
