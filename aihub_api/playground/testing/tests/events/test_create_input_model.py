from typing import Type

import pytest
from pydantic import BaseModel

from aihub_api.events.create_input_model import create_input_model
from playground.testing.tests.events.TestEvent import TestEvent, NestedTestModel, Level2Model, Level3Model


@pytest.fixture
def pydantic_model() -> Type[BaseModel]:
    return create_input_model(TestEvent)


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
        assert isinstance(pydantic_instance.nested_model, NestedTestModel)
        assert pydantic_instance.nested_model.nested_field == "nested_value"
        assert pydantic_instance.nested_model.nested_optional == 123
        assert pydantic_instance.optional_nested is None

    def test_deep_nesting(self, pydantic_instance):
        assert isinstance(pydantic_instance.nested_model.level2, Level2Model)
        assert pydantic_instance.nested_model.level2.level2_data == "level2_value"
        assert isinstance(pydantic_instance.nested_model.level2.level3, Level3Model)
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
        assert all(isinstance(item, NestedTestModel) for item in pydantic_instance.list_of_nested)
        assert pydantic_instance.list_of_nested[0].nested_field == "item1"
        assert pydantic_instance.list_of_nested[1].nested_field == "item2"

    def test_nested_model_validation(self, pydantic_instance_minimal):
        assert isinstance(pydantic_instance_minimal.nested_model, NestedTestModel)
        assert pydantic_instance_minimal.nested_model.nested_field == "nested_value"
        assert pydantic_instance_minimal.nested_model.nested_optional is None

    def test_nested_model_field_type(self, pydantic_model):
        nested_field = pydantic_model.model_fields["nested_model"]
        assert nested_field.annotation == NestedTestModel
