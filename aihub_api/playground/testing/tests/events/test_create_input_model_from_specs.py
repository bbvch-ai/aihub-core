from typing import Type

import pytest
from pydantic import BaseModel

from aihub_api.events.create_input_model import create_input_model, create_input_model_from_specs
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from playground.testing.tests.events.TestEvent import TestEvent


@pytest.fixture
def event_specs() -> EventSpecs:
    return EventSpecs(event_name=TestEvent.event_name_from_class(), event_schema=TestEvent.model_json_schema())


@pytest.fixture
def pydantic_model(event_specs) -> Type[BaseModel]:
    return create_input_model_from_specs(event_specs)


@pytest.fixture
def pydantic_instance(pydantic_model) -> BaseModel:
    return pydantic_model(test_field="test_value")


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

    def test_instance_creation(self, pydantic_instance):
        assert isinstance(pydantic_instance, BaseModel)
        assert pydantic_instance.test_field == "test_value"
        assert pydantic_instance.test_field_with_default == 42
