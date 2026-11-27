"""A request form left open across a deploy is still answered: the reading stored in the run context before locations
named a collection loads as every collection, while the model is still made to give a collection for each location,
with strict structured output and without it."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai.resources.chat.completions.completions import _type_to_response_format
from pydantic import BaseModel

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form import ExtractionRequestForm
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_plain_answer import (
    ExtractionRequestPlainAnswer,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.requested_location import RequestedLocation


def _stored_reading() -> dict[str, Any]:
    """A reading as the release before collections stored it: its locations carry only the path parts."""
    reading = ExtractionRequestAnswer(
        is_table_request=True,
        confirms_sample=False,
        locations=[RequestedLocation(collection=None, path_glob="invoices/**", path_regex=None)],
        fields="item, amount",
        instructions=None,
        calculation=None,
        document_kind=None,
        row_terms=None,
        document_terms=None,
    ).model_dump(mode="json")
    for location in reading["locations"]:
        del location["collection"]
    return reading


def _run_context(stored: dict[str, Any]) -> MagicMock:
    run_context = MagicMock()
    run_context.get = AsyncMock(return_value=stored)
    return run_context


@pytest.mark.asyncio
async def test_a_reading_stored_before_collections_loads_as_every_collection():
    reading = await ExtractionRequestForm.understood(_run_context(_stored_reading()))

    assert reading.locations == [RequestedLocation(collection=None, path_glob="invoices/**", path_regex=None)]
    assert reading.selection.any_of[0].collection is None
    assert reading.selection.any_of[0].path_glob == "invoices/**"


@pytest.mark.asyncio
async def test_a_confirmed_reading_stored_before_collections_loads():
    reading = await ExtractionRequestForm.confirmed(_run_context(_stored_reading()))

    assert reading is not None
    assert reading.locations[0].collection is None


@pytest.mark.parametrize("model", [ExtractionRequestPlainAnswer, ExtractionRequestAnswer])
def test_strict_output_still_requires_a_collection_for_every_location(model: type[BaseModel]):
    schema = _type_to_response_format(model)["json_schema"]
    location = schema["schema"]["$defs"]["RequestedLocation"]

    assert schema["strict"] is True
    assert location["required"] == ["collection", "path_glob", "path_regex"]
    assert "default" not in location["properties"]["collection"]


@pytest.mark.parametrize("model", [ExtractionRequestPlainAnswer, ExtractionRequestAnswer])
def test_the_plain_schema_still_requires_a_collection_for_every_location(model: type[BaseModel]):
    location = model.model_json_schema()["$defs"]["RequestedLocation"]

    assert location["required"] == ["collection", "path_glob", "path_regex"]
    assert "default" not in location["properties"]["collection"]


def test_a_location_without_any_collection_key_is_every_collection_and_an_explicit_one_stays():
    assert RequestedLocation.model_validate({"path_glob": "a/**", "path_regex": None}).collection is None
    named = {"collection": "finance/invoices", "path_glob": None, "path_regex": None}
    assert RequestedLocation.model_validate(named).collection == "finance/invoices"
