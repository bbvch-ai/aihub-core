import html
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Annotated, Any

import bs4
from aihub_lib.generative_ai.document.tables.markdown_table import parse_markdown_table, split_dataframe_into_chunks
from bs4.element import PageElement
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser.interface import NodeParser
from llama_index.core.node_parser.node_utils import build_nodes_from_splits
from llama_index.core.schema import BaseNode, MetadataMode, NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.core.utils import get_tqdm_iterable
from pydantic import ConfigDict, Field, model_validator

from aihub_lib.generative_ai.document.extractors import MetadataExtractor
from aihub_lib.generative_ai.document.loaders.DocumentIntelligenceLoader import PAGE_BREAK
from aihub_lib.generative_ai.document.parsers.Split import Split
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.vectors.node_metadata import (
    DEFAULT_METADATA,
    HEADING_LEVEL,
    INDEX,
    NODE_CONTENT_TYPE,
    NODE_CONTENT_TYPE_FIGURE,
    NODE_CONTENT_TYPE_TABLE,
    NODE_CONTENT_TYPE_TEXT,
    PAGE,
    SECTION_END_LINE,
    SECTION_START_LINE,
    NodeContentType,
)


@dataclass
class MarkdownHeader:
    line_number: int
    hashes: str
    header_text: str

    @property
    def level(self) -> int:
        return len(self.hashes)


@dataclass(frozen=True)
class TextChunk:
    content: str
    content_type: NodeContentType


def find_markdown_headers(content: str) -> list[MarkdownHeader]:
    headers = []
    for line_number, line in enumerate(content.splitlines(), 0):
        stripped_line = line.lstrip()
        if stripped_line.startswith("#"):
            hashes = stripped_line.split()[0]
            header_text = stripped_line[len(hashes) :].strip()
            if set(hashes) == {"#"} and len(hashes) <= 6:
                headers.append(
                    MarkdownHeader(
                        line_number=line_number,
                        hashes=hashes,
                        header_text=header_text,
                    )
                )
    return headers


class MarkdownContentSplitter:
    """
    Splits content into smaller parts based on Markdown headers.
    """

    def __init__(self):
        self.metadata = {}
        self.current_headers: dict[str, any] = {f"h{i}": None for i in range(1, 7)}  # Track current header levels

    def split_content(self, content: str, metadata: dict[str, any] = None) -> list[Split]:
        if metadata:
            self.metadata = {**DEFAULT_METADATA, **metadata}
        else:
            self.metadata = DEFAULT_METADATA.copy()

        content = content.strip()
        if not content:
            return []
        splits = []
        headers = find_markdown_headers(content)

        lines = content.splitlines()

        if headers and headers[0].line_number > 0:
            first_header = headers[0]
            self._update_metadata("", 0)
            splits.append(
                Split(
                    metadata=self.metadata
                    | {
                        SECTION_START_LINE: 0,
                        SECTION_END_LINE: first_header.line_number - 1,
                    },
                    content="\n".join(lines[: first_header.line_number]),
                    level=0,
                )
            )

        for i, header in enumerate(headers):
            self._update_metadata(header.header_text, header.level)

            if i + 1 < len(headers):
                next_header_line = headers[i + 1].line_number
            else:
                next_header_line = len(lines)

            header_content = "\n".join(lines[header.line_number : next_header_line])

            splits.append(
                Split(
                    metadata=self.metadata
                    | {
                        SECTION_START_LINE: header.line_number,
                        SECTION_END_LINE: next_header_line - 1,
                    },
                    content=header_content,
                    level=header.level,
                )
            )

        if not splits:
            self._update_metadata("", 0)
            return [
                Split(
                    metadata=self.metadata | {SECTION_START_LINE: 0, SECTION_END_LINE: len(lines) - 1},
                    content=content,
                    level=0,
                )
            ]

        return splits

    def _update_metadata(self, new_header: str, new_header_level: int) -> None:
        if new_header_level > 0:
            self.current_headers[f"h{new_header_level}"] = new_header

        # Clear lower-level headers if moving to a higher level
        for i in range(new_header_level + 1, 7):
            self.current_headers[f"h{i}"] = None

        self.metadata.update(self.current_headers)
        self.metadata[HEADING_LEVEL] = new_header_level or 0


class NodeCreatorFromSplits:
    """
    Creates nodes from splits. Nodes are linked together using PREV and NEXT relationships based on the header levels.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 20, llm_config: LLMConfig | None = None):
        self.include_metadata = True
        self.metadata = {}
        self.sentence_splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.id_func = None
        self.current_index = 0  # Initialize the index counter
        self.header_references = {}
        self.llm_config = llm_config

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the configured LLM's tokenizer, or estimate based on characters.
        """
        if not self.llm_config:
            # according to OpenAI 1 token is around 4 characters
            return len(text) // 4

        token_list = self.llm_config.token_counter(text)
        return len(token_list)

    def _fallback_table_chunk(self, fallback_text: str) -> list[TextChunk]:
        """
        Create a fallback TextChunk from raw text content, or empty list if text is blank.
        """
        if fallback_text.strip():
            return [TextChunk(fallback_text, NODE_CONTENT_TYPE_TABLE)]
        return []

    def _chunk_table(self, child: PageElement, text_chunks: list[TextChunk]) -> list[TextChunk]:
        """
        Detects if a table needs to be chunked and splits it into separate chunks.

        Tables are expected to be markdown format with headers already correctly set
        by DoclingLoader. This method only handles chunking for large tables.

        Uses shared table utilities from aihub_lib.generative_ai.document.tables.
        """
        markdown_table = child.text.strip()

        if not markdown_table:
            return text_chunks

        token_count = self._count_tokens(markdown_table)

        if token_count <= self.sentence_splitter.chunk_size:
            text_chunks.append(TextChunk(markdown_table, NODE_CONTENT_TYPE_TABLE))
        else:
            text_chunks.extend(self._split_markdown_table(markdown_table))

        return text_chunks

    def _split_markdown_table(self, markdown_table: str) -> list[TextChunk]:
        """
        Split a large markdown table into smaller chunks, preserving headers.

        Uses shared table utilities from aihub_lib.generative_ai.document.tables.
        """
        df = parse_markdown_table(markdown_table)
        if df is None:
            return self._fallback_table_chunk(markdown_table)

        # Maximum reranking context is 4096, therefore half is a good maximum chunk size
        max_tokens = min(2048, self.sentence_splitter.chunk_size * 2)
        chunks = split_dataframe_into_chunks(df, max_tokens, self._count_tokens)

        return [TextChunk(chunk, NODE_CONTENT_TYPE_TABLE) for chunk in chunks]

    def create_nodes_from_splits(
        self,
        splits: list[Split],
        node: BaseNode,
        include_metadata: bool = True,
        metadata: dict[str, any] = None,
        id_func: Callable | None = None,
    ) -> list[TextNode]:
        self.include_metadata = include_metadata
        self.metadata = {**DEFAULT_METADATA, **metadata} if metadata else DEFAULT_METADATA.copy()
        self.id_func = id_func

        nodes: list[TextNode] = []
        last_nodes_stack = []

        page = 1
        for split in splits:
            split.metadata.update({PAGE: page})

            text_chunks: list[TextChunk] = []
            soup = bs4.BeautifulSoup(split.content, "html.parser")
            buffer = ""

            for child in soup.children:
                if isinstance(child, bs4.element.Tag) and child.name in [
                    NODE_CONTENT_TYPE_TABLE,
                    NODE_CONTENT_TYPE_FIGURE,
                ]:
                    if buffer.strip():
                        text_chunks.extend(
                            [
                                TextChunk(text_split, NODE_CONTENT_TYPE_TEXT)
                                for text_split in self.sentence_splitter.split_text(buffer)
                            ]
                        )
                        buffer = ""
                    if child.name == NODE_CONTENT_TYPE_TABLE:
                        text_chunks = self._chunk_table(child, text_chunks)
                    else:
                        text_chunks.append(TextChunk(child.text, child.name))
                else:
                    buffer += str(child)

            if buffer.strip():
                text_chunks.extend(
                    [
                        TextChunk(text_split, NODE_CONTENT_TYPE_TEXT)
                        for text_split in self.sentence_splitter.split_text(buffer)
                    ]
                )

            split_nodes = [self._build_node_from_split(text_chunk, node, split.metadata) for text_chunk in text_chunks]
            self._set_relationships_within_split(split_nodes)
            self._set_relationships_between_splits(split_nodes, split.level, last_nodes_stack)
            nodes.extend(split_nodes)

            if PAGE_BREAK in split.content:
                page += 1

        return nodes

    def _build_node_from_split(self, text_chunk: TextChunk, node: BaseNode, metadata: dict) -> TextNode:
        node = build_nodes_from_splits([text_chunk.content], node, id_func=self.id_func)[0]
        if self.include_metadata:
            metadata[INDEX] = self.current_index
            node.metadata = {**self.metadata, **metadata}
            node.metadata.update({NODE_CONTENT_TYPE: text_chunk.content_type})
        self.current_index += 1
        return node

    @staticmethod
    def _set_relationships_within_split(nodes: list[TextNode]) -> None:
        """
        Set relationships between the nodes within a split. The first node is linked to the second node and so on.
        NEXT relationships are only set between nodes that share the same heading.
        @param nodes: The nodes to set relationships for.
        """
        for prev_node, curr_node in zip(nodes, nodes[1:]):
            # Check if the nodes share the same heading at each level (h1 to h6)
            same_heading = True
            for i in range(1, 7):
                if prev_node.metadata.get(f"h{i}") != curr_node.metadata.get(f"h{i}"):
                    same_heading = False
                    break

            if same_heading:
                curr_node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=prev_node.node_id)
                prev_node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=curr_node.node_id)

    def _set_relationships_between_splits(
        self, nodes: list[TextNode], header_level: int, last_nodes_stack: list
    ) -> None:
        """
        Set relationships between the nodes of the current split and the nodes of the previous split.
        The first node of the current section links to the last node of the previous upper-level section.

        @param nodes: The nodes of the current split.
        @param header_level: The header level of the current split.
        @param last_nodes_stack: Stack of last nodes of the previous splits, keeping track of nodes by header level.
        """
        if not nodes:
            return

        # Find the last node at the upper level
        while last_nodes_stack and last_nodes_stack[-1][0] >= header_level:
            last_nodes_stack.pop()

        # Link the first node in the current section to the last node of the previous upper-level section
        if last_nodes_stack:
            nodes[0].relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=last_nodes_stack[-1][1].node_id)

        # Update the stack with the last node of the current level
        last_nodes_stack.append((header_level, nodes[-1]))


class MarkdownStructuralNodeParser(NodeParser):
    """
    Markdown node parser. Splits a document into Nodes using custom Markdown splitting logic with header levels.
    This is useful for documents with a hierarchical structure. It follows the logic of a reader's way of parsing a
    document.

    PREV and NEXT relationships are set based on header levels:
    - Nodes in a lower level use PREV relationship to link to the previous node in the upper level
    - Nodes inside a section are linked using NEXT and PREV relationships

    If the section content is too large, a simple sentence splitter to split the content into smaller nodes is used.
    All of these nodes are linked together using prev-next relationships.

    The first node of a split links to the last node of the upper level split.

    @example
    Chapter 1:
    Node A (Prev: None, Next: B)
    Node B (Prev: A, Next: None)

    Chapter 1.2
    Node C (Prev: B, Next: D) <-- Here, Node B is the previous, because it is the last node in the upper chapter
    Node D (Prev: C, Next: E)
    Node E (Prev: D, Next: None)

    Chapter 1.3
    Node F (Prev: B, Next: G) <-- Here, Node B is the previous, because it is the last node in the upper chapter
    Node G (Prev: F, Next: H)
    Node H (Prev: G, Next: None)
    """

    metadata: Annotated[dict[str, Any], Field(description="Metadata to include in the nodes.")] = {}
    chunk_size: Annotated[int, Field(description="Maximum number of tokens in a chunk.")] = 512
    chunk_overlap: Annotated[int, Field(description="Number of overlapping tokens between chunks.")] = 20
    include_prev_next_rel: Annotated[bool, Field(description="Include prev/next node relationships.")] = False

    llm_config: Annotated[
        LLMConfig | None, Field(description="LLM configuration for table header detection and tokenization.")
    ] = None

    metadata_extractor: Annotated[
        MetadataExtractor | None, Field(description="MetadataExtractor used to extract metadata.")
    ] = None

    markdown_splitter: Annotated[
        MarkdownContentSplitter,
        Field(
            default_factory=MarkdownContentSplitter,
            description="Markdown content splitter to use for splitting content into smaller nodes.",
        ),
    ]

    node_builder_from_splits: Annotated[
        NodeCreatorFromSplits | None,
        Field(
            description="Node creator from splits.",
        ),
    ] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="before")
    def set_node_builder(cls, values):
        if isinstance(values, dict) and values.get("node_builder_from_splits") is None:
            values["node_builder_from_splits"] = NodeCreatorFromSplits(
                chunk_size=values.get("chunk_size", 512),
                chunk_overlap=values.get("chunk_overlap", 20),
                llm_config=values.get("llm_config", None),
            )
        return values

    @classmethod
    def from_defaults(
        cls,
        include_metadata: bool = True,
        metadata: dict[str, Any] | None = None,
        chunk_size: int = 512,
        chunk_overlap: int = 0,
        callback_manager: CallbackManager | None = None,
    ) -> "MarkdownStructuralNodeParser":
        return cls(
            include_metadata=include_metadata,
            metadata=metadata or DEFAULT_METADATA.copy(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            callback_manager=callback_manager or CallbackManager([]),
        )

    @classmethod
    def class_name(cls) -> str:
        return "MarkdownStructuralNodeParser"

    def _parse_nodes(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
        **kwargs: Any,
    ) -> list[BaseNode]:
        result = []

        for node in get_tqdm_iterable(nodes, show_progress, "Parsing nodes"):
            text_nodes = self.get_nodes_from_node(node)
            result.extend(text_nodes)

        return result

    @trace_fn
    def get_nodes_from_node(self, node: BaseNode) -> list[TextNode]:
        """
        Parse nodes from a markdown node. The node content is split into smaller nodes based on headers.
        The relationships between the nodes are set based on the header levels.
        @param node: The node to parse.
        @return: List of TextNodes.
        """
        text = node.get_content(metadata_mode=MetadataMode.NONE)
        text = html.unescape(text)

        splits = self.markdown_splitter.split_content(text, self.metadata)
        if self.metadata_extractor:
            splits = self.metadata_extractor.extract(splits)
        return self.node_builder_from_splits.create_nodes_from_splits(
            splits, node, self.include_metadata, self.metadata, self.id_func
        )
