from typing import Type

import pytest
from pydantic import BaseModel

from aihub_api.events.EventModelCreationService import EventModelCreationService
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from playground.testing.tests.events.TestEvent import TestEvent, NestedTestModel


class TestDataProvider:
    """Shared test data for all test scenarios"""

    @staticmethod
    def get_complete_instance_data():
        return {
            "test_field": "test_value",
            "nested_model": {
                "nested_field": "nested_value",
                "nested_optional": 123,
                "level2": {"level2_data": "level2_value", "level3": {"deep_value": "deep_test", "deep_number": 777}},
            },
            "union_field": "string_value",
            "complex_union": "complex_string",
            "list_of_nested": [{"nested_field": "item1"}, {"nested_field": "item2"}],
        }

    @staticmethod
    def get_minimal_instance_data():
        return {
            "test_field": "test_value",
            "nested_model": {"nested_field": "nested_value"},
            "union_field": 42,
            "complex_union": {"nested_field": "complex_nested"},
            "list_of_nested": [],
        }


@pytest.fixture
def event_specs() -> EventSpecs:
    return EventSpecs(event_name=TestEvent.event_name_from_class(), event_schema=TestEvent.model_json_schema())


@pytest.fixture(params=["class", "specs"])
def input_model_factory(request, event_specs):
    """Factory that creates input models using both methods"""
    if request.param == "class":
        return lambda: EventModelCreationService.create_input_model(TestEvent), "class"
    else:
        return lambda: EventModelCreationService.create_input_model_from_specs(event_specs), "specs"


@pytest.fixture(params=["class", "specs"])
def output_model_factory(request, event_specs):
    """Factory that creates output models using both methods"""
    if request.param == "class":
        return lambda: EventModelCreationService.create_output_model(TestEvent), "class"
    else:
        return lambda: EventModelCreationService.create_output_model_from_specs(event_specs), "specs"


@pytest.fixture
def input_model(input_model_factory) -> Type[BaseModel]:
    factory, _ = input_model_factory
    return factory()


@pytest.fixture
def output_model(output_model_factory) -> Type[BaseModel]:
    factory, _ = output_model_factory
    return factory()


@pytest.fixture
def input_instance_complete(input_model) -> BaseModel:
    return input_model(**TestDataProvider.get_complete_instance_data())


@pytest.fixture
def input_instance_minimal(input_model) -> BaseModel:
    return input_model(**TestDataProvider.get_minimal_instance_data())


@pytest.fixture
def output_instance_complete(output_model) -> BaseModel:
    return output_model(**TestDataProvider.get_complete_instance_data())


@pytest.fixture
def output_instance_minimal(output_model) -> BaseModel:
    return output_model(**TestDataProvider.get_minimal_instance_data())


class TestModelCreation:
    """Tests for basic model creation and naming"""

    def test_input_model_creation(self, input_model):
        assert input_model is not None
        assert issubclass(input_model, BaseModel)

    def test_output_model_creation(self, output_model):
        assert output_model is not None
        assert issubclass(output_model, BaseModel)

    def test_input_model_name(self, input_model):
        assert input_model.__name__ == f"{TestEvent.event_name_from_class()}Input"

    def test_output_model_name(self, output_model):
        assert output_model.__name__ == f"{TestEvent.event_name_from_class()}Output"


class TestFieldExclusion:
    """Tests for proper field exclusion in input and output models"""

    INPUT_EXCLUDED = {"event_id", "created_at", "user", "locale", "display_name", "display_description"}
    OUTPUT_EXCLUDED = {"event_id", "created_at", "_event_name", "_parent_event_names"}

    def test_input_model_excluded_fields(self, input_model):
        for field in self.INPUT_EXCLUDED:
            assert field not in input_model.model_fields, f"Field {field} should be excluded from input model"

    def test_output_model_excluded_fields(self, output_model):
        for field in self.OUTPUT_EXCLUDED:
            assert field not in output_model.model_fields, f"Field {field} should be excluded from output model"

    def test_input_model_included_fields(self, input_model):
        expected_fields = {
            "test_field",
            "test_field_with_default",
            "nested_model",
            "optional_nested",
            "union_field",
            "complex_union",
            "list_of_nested",
            "optional_union",
        }
        for field in expected_fields:
            assert field in input_model.model_fields, f"Field {field} should be included in input model"

    def test_output_model_included_fields(self, output_model):
        expected_fields = {
            "test_field",
            "test_field_with_default",
            "nested_model",
            "optional_nested",
            "union_field",
            "complex_union",
            "list_of_nested",
            "optional_union",
        }
        for field in expected_fields:
            assert field in output_model.model_fields, f"Field {field} should be included in output model"


class TestInstanceCreation:
    """Tests for creating instances of generated models"""

    def test_input_instance_creation(self, input_instance_complete):
        assert isinstance(input_instance_complete, BaseModel)
        assert input_instance_complete.test_field == "test_value"
        assert input_instance_complete.test_field_with_default == 42
        assert input_instance_complete.optional_nested is None

    def test_output_instance_creation(self, output_instance_complete):
        assert isinstance(output_instance_complete, BaseModel)
        assert output_instance_complete.test_field == "test_value"
        assert output_instance_complete.test_field_with_default == 42
        assert output_instance_complete.optional_nested is None

    def test_minimal_instance_creation(self, input_instance_minimal, output_instance_minimal):
        # Test both input and output models work with minimal data
        for instance in [input_instance_minimal, output_instance_minimal]:
            assert instance.test_field == "test_value"
            assert instance.union_field == 42
            assert len(instance.list_of_nested) == 0


class TestNestedModels:
    """Tests for nested model handling"""

    def test_nested_model_structure(self, input_instance_complete, input_model_factory):
        _, creation_method = input_model_factory
        nested_model = input_instance_complete.nested_model

        if creation_method == "class":
            # When created from class, we get the actual NestedTestModel type
            assert isinstance(nested_model, NestedTestModel)
        else:
            # When created from specs, we get dynamically created models
            assert hasattr(nested_model, "nested_field")
            assert hasattr(nested_model, "nested_optional")

        assert nested_model.nested_field == "nested_value"
        assert nested_model.nested_optional == 123

    def test_deep_nesting(self, input_instance_complete, output_instance_complete):
        for instance in [input_instance_complete, output_instance_complete]:
            level2 = instance.nested_model.level2
            assert level2.level2_data == "level2_value"

            level3 = level2.level3
            assert level3.deep_value == "deep_test"
            assert level3.deep_number == 777

    def test_nested_model_field_types(self, input_model, input_model_factory):
        _, creation_method = input_model_factory
        nested_field = input_model.model_fields["nested_model"]

        if creation_method == "class":
            assert nested_field.annotation == NestedTestModel
        else:
            # For specs-based creation, we get dynamically created types
            assert isinstance(nested_field.annotation, type)
            assert issubclass(nested_field.annotation, BaseModel)


class TestUnionTypes:
    """Tests for union type handling"""

    def test_string_union(self, input_instance_complete, output_instance_complete):
        for instance in [input_instance_complete, output_instance_complete]:
            assert instance.union_field == "string_value"

    def test_integer_union(self, input_instance_minimal, output_instance_minimal):
        for instance in [input_instance_minimal, output_instance_minimal]:
            assert instance.union_field == 42

    def test_complex_union_string(self, input_instance_complete, output_instance_complete):
        for instance in [input_instance_complete, output_instance_complete]:
            assert instance.complex_union == "complex_string"

    def test_complex_union_nested(self, input_instance_minimal, output_instance_minimal):
        for instance in [input_instance_minimal, output_instance_minimal]:
            assert hasattr(instance.complex_union, "nested_field")
            assert instance.complex_union.nested_field == "complex_nested"


class TestListHandling:
    """Tests for list of nested models"""

    def test_list_of_nested(self, input_instance_complete, output_instance_complete):
        for instance in [input_instance_complete, output_instance_complete]:
            assert len(instance.list_of_nested) == 2
            assert instance.list_of_nested[0].nested_field == "item1"
            assert instance.list_of_nested[1].nested_field == "item2"

    def test_empty_list(self, input_instance_minimal, output_instance_minimal):
        for instance in [input_instance_minimal, output_instance_minimal]:
            assert len(instance.list_of_nested) == 0


class TestSchemaValidation:
    """Tests specific to schema-based model creation"""

    def test_schema_structure(self, event_specs):
        schema = event_specs.event_schema
        assert "properties" in schema
        assert "$defs" in schema

        # Check nested model reference
        nested_prop = schema["properties"]["nested_model"]
        assert "$ref" in nested_prop
        assert nested_prop["$ref"] == "#/$defs/NestedTestModel"

    def test_nested_definitions(self, event_specs):
        defs = event_specs.event_schema["$defs"]

        # Check NestedTestModel definition
        nested_def = defs["NestedTestModel"]
        assert nested_def["type"] == "object"
        assert "nested_field" in nested_def["properties"]
        assert "level2" in nested_def["properties"]

    def test_deep_nesting_definitions(self, event_specs):
        defs = event_specs.event_schema["$defs"]

        # Check Level2Model
        level2_def = defs["Level2Model"]
        assert "level3" in level2_def["properties"]
        assert level2_def["properties"]["level3"]["$ref"] == "#/$defs/Level3Model"

        # Check Level3Model
        level3_def = defs["Level3Model"]
        assert "deep_value" in level3_def["properties"]
        assert "deep_number" in level3_def["properties"]

    def test_union_schema(self, event_specs):
        schema = event_specs.event_schema
        union_prop = schema["properties"]["union_field"]

        assert "anyOf" in union_prop
        types = [item.get("type") for item in union_prop["anyOf"]]
        assert "string" in types
        assert "integer" in types
