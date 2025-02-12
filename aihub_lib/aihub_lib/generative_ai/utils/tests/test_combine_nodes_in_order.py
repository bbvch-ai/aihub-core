import pytest
from llama_index.core.base.llms.types import ChatMessage
from pytest_bdd import given, scenarios, then, when

from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.semantic.retriever import Document
from aihub_lib.persistence.rag.vectors.node_metadata import (
    SECTION_START_LINE,
    SOURCE,
    NAMESPACE,
    LANGUAGE,
    TYPE,
    VERSION,
    CREATED_AT,
    UPDATED_AT,
    INSERTED_AT,
)

scenarios("./features/combine_nodes_in_order.feature")


@pytest.fixture
def locale_handler():
    class MockLocaleHandler(LocaleHandler):
        def __call__(self, key: str):
            if key == "agent.prompt.rag.context_prompt":
                return "Default prompt: {context_str}"
            return super().__call__(key)

    return MockLocaleHandler(locale="en")


@pytest.fixture
def no_context_prompt():
    return None


@pytest.fixture
def custom_prompt():
    return "Custom prompt: {context_str}"


@given("a locale handler", target_fixture="the_locale_handler")
def _(locale_handler):
    return locale_handler


@given("no context prompt", target_fixture="the_context_prompt")
def _(no_context_prompt):
    return no_context_prompt


@given("a custom context prompt", target_fixture="the_context_prompt")
def _(custom_prompt):
    return custom_prompt


@given("the following context nodes:", target_fixture="the_context_nodes")
def _(datatable):
    context_nodes = []
    headers = datatable[0]
    metadata_fields = [
        NAMESPACE,
        SOURCE,
        TYPE,
        LANGUAGE,
        VERSION,
        CREATED_AT,
        UPDATED_AT,
        INSERTED_AT,
        SECTION_START_LINE,
    ]

    for row in datatable[1:]:
        metadata = {
            column: (int(row[index]) if column == "section_start_line" else row[index])
            for index, column in enumerate(headers)
            if row[index] and column in metadata_fields
        }

        text = row[headers.index("text")]
        score = float(row[headers.index("score")])

        context_nodes.append(
            Document(
                id=f"{metadata.get(SOURCE, 'missing')}-{metadata.get(SECTION_START_LINE, 0)}",
                score=score,
                content=text,
                metadata=metadata,
            )
        )

    return context_nodes


@given("no context nodes", target_fixture="the_context_nodes")
def _():
    return []


@when("the combine_nodes_in_order function is called", target_fixture="the_result")
def _(the_context_nodes, the_locale_handler, the_context_prompt):
    try:
        return combine_nodes_in_order(
            context_nodes=the_context_nodes, locale_handler=the_locale_handler, context_prompt=the_context_prompt
        )
    except ValueError as e:
        return e


@then("it should return:")
def _(the_result, docstring):
    assert isinstance(the_result, ChatMessage)
    expected = docstring.strip()
    actual = the_result.content.strip()
    assert actual == expected, f"\nExpected:\n{expected}\n\nBut got:\n{actual}\n"


@then("a ValueError is raised")
def _(the_context_nodes, the_locale_handler, the_context_prompt):
    with pytest.raises(ValueError, match=r".*metadata.*source"):
        combine_nodes_in_order(
            context_nodes=the_context_nodes, locale_handler=the_locale_handler, context_prompt=the_context_prompt
        )
