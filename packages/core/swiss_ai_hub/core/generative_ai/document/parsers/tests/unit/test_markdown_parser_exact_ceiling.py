"""With an embedding model that declares its tokenizer, every node the parser emits must fit the model exactly as
embed_nodes sends it: content within MAX_NODE_TOKENS and the EMBED text, metadata included, within the window. An
oversized node is otherwise rejected by bge-m3 and skipped, leaving a hole in the index (a code figure did, #1856)."""

from pathlib import Path
from time import time

import pytest
from llama_index.core.schema import Document, MetadataMode, TextNode

from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
    MAX_NODE_TOKENS,
    MarkdownStructuralNodeParser,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    INDEX,
    INSERTED_AT,
    NAMESPACE,
    NODE_CONTENT_TYPE,
    SOURCE,
    UPDATED_AT,
)

WINDOW = 8192
OVERHEAD = 2
DECLARED = {
    "mode": "embedding",
    "max_input_tokens": WINDOW,
    "aihub_tokenizer": "bge-m3",
    "aihub_input_overhead_tokens": 2,
}
PARSERS_SOURCE = Path(__file__).resolve().parents[2]


@pytest.fixture
def parser(monkeypatch) -> MarkdownStructuralNodeParser:
    monkeypatch.setattr(EmbeddingModelConfig, "get_model_info", lambda self: {"model_info": DECLARED})
    metadata = {
        NAMESPACE: "test",
        SOURCE: "contract.md",
        CREATED_AT: int(time()),
        UPDATED_AT: int(time()),
        INSERTED_AT: int(time()),
    }
    return MarkdownStructuralNodeParser(metadata=metadata, embedding_model_name="embedding/bge-m3")


def _count(text: str) -> int:
    return ModelTokenizer.shared("bge-m3").count(text)


def _embed_tokens(node: TextNode) -> int:
    return _count(node.get_content(metadata_mode=MetadataMode.EMBED)) + OVERHEAD


def _assert_every_node_fits(nodes: list[TextNode]) -> None:
    assert all(_count(node.text) <= MAX_NODE_TOKENS for node in nodes)
    assert all(_embed_tokens(node) <= WINDOW for node in nodes)


def test_code_figure_is_split_to_the_exact_cap(parser: MarkdownStructuralNodeParser) -> None:
    source = (PARSERS_SOURCE / "markdown_structural_node_parser.py").read_text(encoding="utf-8")
    # Comment lines would read as markdown headings and markup as HTML, which a figure of code never contains.
    code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#") and "<" not in line)

    nodes = parser.get_nodes_from_node(Document(text=f"# Listing\n<figure>{code}</figure>"))

    figure_nodes = [node for node in nodes if node.metadata.get(NODE_CONTENT_TYPE) == "figure"]
    assert len(figure_nodes) > 1
    _assert_every_node_fits(nodes)


def test_unparseable_table_is_split_to_the_exact_cap(parser: MarkdownStructuralNodeParser) -> None:
    digits = " ".join(str(number * 7919) for number in range(6000))

    nodes = parser.get_nodes_from_node(Document(text=f"# Figures\n<table>{digits}</table>"))

    table_nodes = [node for node in nodes if node.metadata.get(NODE_CONTENT_TYPE) == "table"]
    assert len(table_nodes) > 1
    _assert_every_node_fits(nodes)


def test_large_metadata_shrinks_the_content_so_the_embed_text_fits(parser: MarkdownStructuralNodeParser) -> None:
    """A heading line sits in every node of its section as h1; with ~6k tokens of it a 2048-token piece is over."""
    heading = " ".join(f"Paragraph{number}" for number in range(2000))
    body = "Die Kündigungsfrist beträgt drei Monate zum Monatsende. " * 500

    nodes = parser.get_nodes_from_node(Document(text=f"# {heading}\n{body}"))

    _assert_every_node_fits(nodes)
    assert [node.metadata[INDEX] for node in nodes] == list(range(len(nodes)))
    assert max(_embed_tokens(node) for node in nodes) > WINDOW - 300


def test_metadata_leaving_no_room_for_content_raises_naming_document_and_keys(
    parser: MarkdownStructuralNodeParser,
) -> None:
    heading = " ".join(f"Paragraph{number}" for number in range(3000))
    document = Document(text=f"# {heading}\nShort body.")

    with pytest.raises(ValueError, match=r"contract\.md.*h1 \(\d+ tokens\)"):
        parser.get_nodes_from_node(document)


def test_ordinary_text_keeps_its_512_token_splits(parser: MarkdownStructuralNodeParser) -> None:
    """The text splitter stays in tiktoken, so chunk boundaries of existing indexes do not move."""
    body = "The notice period is three months to the end of a month. " * 300
    fallback = MarkdownStructuralNodeParser(metadata={SOURCE: "contract.md"})

    exact_nodes = parser.get_nodes_from_node(Document(text=f"# Terms\n{body}"))
    fallback_nodes = fallback.get_nodes_from_node(Document(text=f"# Terms\n{body}"))

    assert [node.text for node in exact_nodes] == [node.text for node in fallback_nodes]
