from types import UnionType
from typing import Union, get_args, get_origin

import pytest
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.BaseEvent import BaseEvent
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentClassDiscoveryResponseEvent,
    AgentConfigSpecs,
    EventSpecs,
)
from pydantic import BaseModel

from aihub_api.services.ModelCreationService import ModelCreationService
from playground.testing.tests.services.TestEvent import Level2Model, Level3Model, NestedTestModel, TestEvent


def is_union_type(origin) -> bool:
    """Check if the origin is a union type (either UnionType or typing.Union)"""
    return origin is UnionType or origin is Union


def unwrap_annotated(type_annotation):
    """Unwrap Annotated types to get the inner type"""
    from typing import Annotated
    from typing import get_args as typing_get_args
    from typing import get_origin as typing_get_origin

    origin = typing_get_origin(type_annotation)
    if origin is Annotated:
        # Return the first arg which is the actual type
        return typing_get_args(type_annotation)[0]
    return type_annotation


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
    return EventSpecs.from_event_class(TestEvent)


@pytest.fixture(params=["class", "specs"])
def input_model_factory(request, event_specs):
    """Factory that creates input models using both methods"""
    if request.param == "class":
        return lambda: ModelCreationService.create_input_model_from_event_class(TestEvent), "class"
    else:
        return lambda: ModelCreationService.create_input_model_from_event_specs(event_specs), "specs"


@pytest.fixture(params=["class", "specs"])
def output_model_factory(request, event_specs):
    """Factory that creates output models using both methods"""
    if request.param == "class":
        return lambda: ModelCreationService.create_output_model_from_event_class(TestEvent), "class"
    else:
        return lambda: ModelCreationService.create_output_model_from_event_specs(event_specs), "specs"


@pytest.fixture
def input_model(input_model_factory) -> type[BaseModel]:
    factory, _ = input_model_factory
    return factory()


@pytest.fixture
def output_model(output_model_factory) -> type[BaseModel]:
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


class TestFieldTyping:
    """Tests to ensure all field types and annotations are correctly preserved"""

    def test_basic_field_types(self, input_model, output_model):
        """Test basic string and int field types"""
        for model in [input_model, output_model]:
            # Test required string field
            test_field = model.model_fields["test_field"]
            assert test_field.annotation is str
            assert test_field.is_required()

            # Test int field with default
            test_field_default = model.model_fields["test_field_with_default"]
            assert test_field_default.annotation is int
            assert not test_field_default.is_required()
            assert test_field_default.default == 42

    def test_nested_model_types(self, input_model, output_model, input_model_factory):
        """Test nested model field types"""
        _, creation_method = input_model_factory

        for model in [input_model, output_model]:
            # Required nested model
            nested_field = model.model_fields["nested_model"]
            # Both class and specs-based creation result in BaseModel subclasses
            assert isinstance(nested_field.annotation, type)
            assert issubclass(nested_field.annotation, BaseModel)
            # For class-based, verify the name matches
            if creation_method == "class":
                assert nested_field.annotation.__name__ == "NestedTestModel"
            assert nested_field.is_required()

            # Optional nested model
            optional_nested_field = model.model_fields["optional_nested"]
            assert not optional_nested_field.is_required()
            assert optional_nested_field.default is None

            # Check union structure for optional field
            origin = get_origin(optional_nested_field.annotation)
            if is_union_type(origin):
                args = get_args(optional_nested_field.annotation)
                # Unwrap Annotated types from Pydantic schema reconstruction
                unwrapped_args = [unwrap_annotated(arg) for arg in args]
                assert len(unwrapped_args) == 2
                assert type(None) in unwrapped_args
                # Other arg should be a BaseModel subclass
                non_none_args = [arg for arg in unwrapped_args if arg is not type(None)]
                assert len(non_none_args) == 1
                assert isinstance(non_none_args[0], type)
                assert issubclass(non_none_args[0], BaseModel)

    def test_union_field_types(self, input_model, output_model):
        """Test union type fields"""
        for model in [input_model, output_model]:
            # Simple union: str | int
            union_field = model.model_fields["union_field"]
            origin = get_origin(union_field.annotation)
            args = get_args(union_field.annotation)
            assert is_union_type(origin)
            # Unwrap Annotated types from Pydantic schema reconstruction
            unwrapped_args = [unwrap_annotated(arg) for arg in args]
            assert str in unwrapped_args
            assert int in unwrapped_args
            assert union_field.is_required()

            # Optional union: Optional[str | int]
            optional_union_field = model.model_fields["optional_union"]
            assert not optional_union_field.is_required()
            assert optional_union_field.default is None

            # Check the inner union type
            if is_union_type(get_origin(optional_union_field.annotation)):
                args = get_args(optional_union_field.annotation)
                # Should be str | int | None or similar (unwrap Annotated)
                unwrapped_args = [unwrap_annotated(arg) for arg in args]
                assert type(None) in unwrapped_args

    def test_complex_union_types(self, input_model, output_model, input_model_factory):
        """Test union types with nested models"""
        _, creation_method = input_model_factory

        for model in [input_model, output_model]:
            complex_union_field = model.model_fields["complex_union"]
            origin = get_origin(complex_union_field.annotation)
            args = get_args(complex_union_field.annotation)

            assert is_union_type(origin)
            # Unwrap Annotated types from Pydantic schema reconstruction
            unwrapped_args = [unwrap_annotated(arg) for arg in args]
            assert str in unwrapped_args
            # One of the args should be a BaseModel subclass (dynamically created)
            nested_types = [arg for arg in unwrapped_args if isinstance(arg, type) and issubclass(arg, BaseModel)]
            assert len(nested_types) >= 1
            # For class-based, verify the nested type name
            if creation_method == "class":
                assert any(arg.__name__ == "NestedTestModel" for arg in nested_types)
            assert complex_union_field.is_required()

    def test_list_field_types(self, input_model, output_model, input_model_factory):
        """Test list type fields"""
        _, creation_method = input_model_factory

        for model in [input_model, output_model]:
            list_field = model.model_fields["list_of_nested"]
            origin = get_origin(list_field.annotation)
            args = get_args(list_field.annotation)

            assert origin is list
            assert len(args) == 1

            # The list element should be a BaseModel subclass (dynamically created)
            assert isinstance(args[0], type)
            assert issubclass(args[0], BaseModel)
            # For class-based, verify the element type name
            if creation_method == "class":
                assert args[0].__name__ == "NestedTestModel"
            assert list_field.is_required()

    def test_nested_model_field_types(self, input_model_factory):
        """Test field types within nested models"""
        input_model, creation_method = input_model_factory

        if creation_method == "class":
            # Test NestedTestModel field types
            assert NestedTestModel.model_fields["nested_field"].annotation is str
            assert NestedTestModel.model_fields["nested_field"].is_required()

            nested_optional = NestedTestModel.model_fields["nested_optional"]
            origin = get_origin(nested_optional.annotation)
            args = get_args(nested_optional.annotation)
            assert is_union_type(origin)
            assert int in args
            assert type(None) in args
            assert not nested_optional.is_required()
            assert nested_optional.default is None

            # Test Level2Model field types
            assert Level2Model.model_fields["level2_data"].annotation is str
            assert Level2Model.model_fields["level2_data"].is_required()
            assert Level2Model.model_fields["level3"].annotation is Level3Model
            assert Level2Model.model_fields["level3"].is_required()

            # Test Level3Model field types
            assert Level3Model.model_fields["deep_value"].annotation is str
            assert Level3Model.model_fields["deep_value"].is_required()
            assert Level3Model.model_fields["deep_number"].annotation is int
            assert not Level3Model.model_fields["deep_number"].is_required()
            assert Level3Model.model_fields["deep_number"].default == 999

    def test_field_defaults_preservation(self, input_model, output_model):
        """Test that default values are correctly preserved"""
        for model in [input_model, output_model]:
            # Field with explicit default
            default_field = model.model_fields["test_field_with_default"]
            assert default_field.default == 42

            # Optional fields with None default
            optional_nested = model.model_fields["optional_nested"]
            assert optional_nested.default is None

            optional_union = model.model_fields["optional_union"]
            assert optional_union.default is None

    def test_required_vs_optional_fields(self, input_model, output_model):
        """Test that required/optional status is correctly preserved"""
        for model in [input_model, output_model]:
            # Required fields
            required_fields = ["test_field", "nested_model", "union_field", "complex_union", "list_of_nested"]
            for field_name in required_fields:
                field = model.model_fields[field_name]
                assert field.is_required(), f"Field {field_name} should be required"

            # Optional fields
            optional_fields = ["test_field_with_default", "optional_nested", "optional_union"]
            for field_name in optional_fields:
                field = model.model_fields[field_name]
                assert not field.is_required(), f"Field {field_name} should be optional"

    def test_type_annotation_consistency(self, input_model, output_model):
        """Test that input and output models have consistent type annotations"""
        input_fields = input_model.model_fields
        output_fields = output_model.model_fields

        # All fields present in both models should have the same type annotations
        common_fields = set(input_fields.keys()) & set(output_fields.keys())

        for field_name in common_fields:
            input_field = input_fields[field_name]
            output_field = output_fields[field_name]

            # For basic types, annotations should be identical
            if input_field.annotation in (str, int, float, bool):
                assert (
                    input_field.annotation == output_field.annotation
                ), f"Field {field_name} has inconsistent basic type annotations"

            # For complex types, check structural equivalence
            else:
                input_origin = get_origin(input_field.annotation)
                output_origin = get_origin(output_field.annotation)

                if input_origin is not None or output_origin is not None:
                    # Both should have the same origin (UnionType, list, etc.)
                    # Special case: UnionType and Union are equivalent
                    if is_union_type(input_origin) and is_union_type(output_origin):
                        pass  # Both are union types, this is fine
                    else:
                        assert input_origin == output_origin, f"Field {field_name} has different generic origins"

                    # For nested models and complex types, verify structural compatibility
                    input_args = get_args(input_field.annotation)
                    output_args = get_args(output_field.annotation)
                    assert len(input_args) == len(
                        output_args
                    ), f"Field {field_name} has different number of type arguments"

                else:
                    # Both should be BaseModel subclasses with same name
                    if isinstance(input_field.annotation, type) and issubclass(input_field.annotation, BaseModel):
                        assert isinstance(
                            output_field.annotation, type
                        ), f"Field {field_name} type mismatch: input is BaseModel, output is not"
                        assert issubclass(
                            output_field.annotation, BaseModel
                        ), f"Field {field_name} output type is not BaseModel subclass"
                        assert (
                            input_field.annotation.__name__ == output_field.annotation.__name__
                        ), f"Field {field_name} BaseModel names don't match"

            # Compare required status
            assert (
                input_field.is_required() == output_field.is_required()
            ), f"Field {field_name} has inconsistent required status between input and output models"

            # Compare defaults
            assert (
                input_field.default == output_field.default
            ), f"Field {field_name} has inconsistent defaults between input and output models"

    def test_python_version_compatibility(self, input_model, output_model):
        """Test that type annotations work correctly across Python versions"""
        for model in [input_model, output_model]:
            for field_name, field in model.model_fields.items():
                # Ensure annotation is not None and is a valid type
                assert field.annotation is not None, f"Field {field_name} has None annotation"

                # Test that we can get origin and args without errors
                try:
                    get_origin(field.annotation)
                    get_args(field.annotation)
                    # These should not raise exceptions
                except Exception as e:
                    pytest.fail(f"Failed to get origin/args for field {field_name}: {e}")

    def test_generic_type_preservation(self, input_model, output_model):
        """Test that generic types (list, UnionType, Optional) are correctly preserved"""
        for model in [input_model, output_model]:
            # Test list type
            list_field = model.model_fields["list_of_nested"]
            assert get_origin(list_field.annotation) is list, list

            # Test Union types
            union_field = model.model_fields["union_field"]
            assert is_union_type(get_origin(union_field.annotation))

            complex_union_field = model.model_fields["complex_union"]
            assert is_union_type(get_origin(complex_union_field.annotation))


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

    def test_event_parents_field_population(self, event_specs):
        """Test that EventSpecs.event_parents contains the correct inheritance hierarchy"""
        # TestEvent directly inherits from BaseEvent, so event_parents should contain only 'TestEvent'
        assert event_specs.event_parents == ["TestEvent"]

        # Verify it matches what the actual event instance would have
        test_event_instance = TestEvent(
            test_field="test",
            nested_model={"nested_field": "nested"},
            union_field="union",
            complex_union="complex",
            list_of_nested=[],
        )
        assert event_specs.event_parents == test_event_instance._parent_event_names

    def test_agent_discovery_response_event_serialization(self, event_specs):
        agent_config = AgentConfig(
            agent_id="test_agent",
            agent_class="TestAgent",
            name=LocaleString(en="Test Agent"),
            description=LocaleString(en="Test agent description"),
        )
        discovery_event = AgentClassDiscoveryResponseEvent(
            agent_class="TestAgent",
            name=agent_config.name,
            description=agent_config.description,
            icon=agent_config.icon,
            is_conversational=False,
            start_events=[event_specs],
            stop_events=[],
            network_graph=WorkflowGraph(directed=True, multigraph=False, graph={}, nodes=[], links=[]),
            form=agent_config.to_formkit_form(),
            agent_config_specs=AgentConfigSpecs.from_agent_config(agent_config, agent_class="TestAgent"),
            hitl_request_events=[],
            hitl_response_events=[],
        )

        # Serialize the event
        serialized = discovery_event.model_dump()

        # Verify the serialized event includes the event_parents field in start_events
        assert "start_events" in serialized
        assert len(serialized["start_events"]) == 1

        event_spec_data = serialized["start_events"][0]
        assert "event_parents" in event_spec_data
        assert event_spec_data["event_parents"] == ["TestEvent"]

    def test_base_event_deserialization_preserves_event_parents(self):
        """Test that BaseEvent deserialization preserves the event_parents field"""
        # Create a TestEvent instance
        original_event = TestEvent(
            test_field="test_value",
            nested_model={"nested_field": "nested_value"},
            union_field="test_union",
            complex_union="test_complex",
            list_of_nested=[],
        )

        # Serialize the event to a dictionary (like AgentEndpointsDiscoveryService does)
        serialized_data = original_event.model_dump()

        # Deserialize using BaseEvent.deserialize_event with dict (like AgentEndpointsDiscoveryService)
        deserialized_event = BaseEvent.deserialize_event(serialized_data)

        # Verify the deserialized event preserves the event_parents field
        assert deserialized_event._event_name == "TestEvent"
        assert deserialized_event._parent_event_names == ["TestEvent"]
        assert deserialized_event._parent_event_names == original_event._parent_event_names

        # Verify other fields are preserved
        assert deserialized_event.test_field == "test_value"
        assert deserialized_event.nested_model.nested_field == "nested_value"
        assert deserialized_event.union_field == "test_union"
        assert deserialized_event.complex_union == "test_complex"
        assert len(deserialized_event.list_of_nested) == 0

    def test_unknown_event_deserialization_preserves_event_parents(self):
        """Test that unknown event deserialization preserves the event_parents field"""
        # Create a dictionary representing an unknown event type with event_parents
        # (like AgentEndpointsDiscoveryService)
        unknown_event_data = {
            "_event_name": "UnknownTestEvent",
            "event_id": "test_id_123",
            "created_at": 1234567890,
            "_parent_event_names": ["UnknownTestEvent", "SomeParentEvent", "BaseEvent"],
            "custom_field": "custom_value",
            "test_field": "test_value",
        }

        # Deserialize using BaseEvent.deserialize_event with dict (like AgentEndpointsDiscoveryService)
        deserialized_event = BaseEvent.deserialize_event(unknown_event_data)

        # Verify the deserialized event preserves the event_parents field
        assert deserialized_event._event_name == "UnknownTestEvent"
        assert deserialized_event._parent_event_names == ["UnknownTestEvent", "SomeParentEvent", "BaseEvent"]

        # Verify custom fields are preserved
        assert deserialized_event.model_dump()["custom_field"] == "custom_value"
        assert deserialized_event.model_dump()["test_field"] == "test_value"

        # Verify the event ID and timestamp are preserved
        assert deserialized_event.event_id == "test_id_123"
        assert deserialized_event.created_at == 1234567890

    def test_complete_event_chain_preserves_event_parents(self):
        """Test the complete chain: TestEvent -> EventSpecs -> PydanticModel -> TestEvent"""
        # Step 1: Create original TestEvent instance
        original_event = TestEvent(
            test_field="chain_test",
            nested_model={"nested_field": "chain_nested", "nested_optional": 42},
            union_field=123,
            complex_union={"nested_field": "chain_complex"},
            list_of_nested=[{"nested_field": "item1"}, {"nested_field": "item2"}],
        )

        # Step 2: Convert TestEvent to EventSpecs
        event_specs = EventSpecs.from_event_class(TestEvent)

        # Verify EventSpecs contains correct event_parents
        assert event_specs.event_parents == ["TestEvent"]
        assert event_specs.event_name == "TestEvent"

        # Step 3: Create Pydantic input model from EventSpecs
        input_model = ModelCreationService.create_input_model_from_event_specs(event_specs)

        # Step 4: Create input model instance from original event data
        original_data = original_event.model_dump()
        # Remove fields that are excluded from input models
        excluded_fields = ModelCreationService._input_excluded_fields
        input_data = {k: v for k, v in original_data.items() if k not in excluded_fields}

        input_instance = input_model(**input_data)

        # Step 5: Convert back to full event data (simulate AgentEndpointsDiscoveryService pattern)
        full_event_data = {
            "event_id": "chain_test_id",
            "created_at": 1234567890,
            "_event_name": "TestEvent",
            "_parent_event_names": event_specs.event_parents,
            **input_instance.model_dump(),
        }

        # Step 6: Deserialize using BaseEvent to get TestEvent back
        final_event = BaseEvent.deserialize_event(full_event_data)

        # Verify the complete chain preserved everything correctly
        assert isinstance(final_event, TestEvent)
        assert final_event._event_name == "TestEvent"
        assert final_event._parent_event_names == ["TestEvent"]
        assert final_event._parent_event_names == original_event._parent_event_names

        # Verify all field values are preserved
        assert final_event.test_field == "chain_test"
        assert final_event.nested_model.nested_field == "chain_nested"
        assert final_event.nested_model.nested_optional == 42
        assert final_event.union_field == 123
        assert final_event.complex_union.nested_field == "chain_complex"
        assert len(final_event.list_of_nested) == 2
        assert final_event.list_of_nested[0].nested_field == "item1"
        assert final_event.list_of_nested[1].nested_field == "item2"

        # Verify that the final event can be serialized/deserialized again
        reserialized_data = final_event.model_dump()
        final_deserialized = BaseEvent.deserialize_event(reserialized_data)
        assert final_deserialized._parent_event_names == ["TestEvent"]
