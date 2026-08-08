from time import time

import pytest
from llama_index.core.schema import Document, NodeRelationship

from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK
from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
    MarkdownStructuralNodeParser,
)
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    INDEX,
    INSERTED_AT,
    NAMESPACE,
    NODE_CONTENT_TYPE,
    SOURCE,
    UPDATED_AT,
)


@pytest.fixture
def node_parser():
    metadata = {
        NAMESPACE: "test",
        SOURCE: "test.md",
        CREATED_AT: int(time()),
        UPDATED_AT: int(time()),
        INSERTED_AT: int(time()),
    }
    return MarkdownStructuralNodeParser(metadata=metadata)


@pytest.fixture
def node_parser_with_chunk_size():
    metadata = {
        NAMESPACE: "test",
        SOURCE: "test.md",
        CREATED_AT: int(time()),
        UPDATED_AT: int(time()),
        INSERTED_AT: int(time()),
    }
    return MarkdownStructuralNodeParser(metadata=metadata, chunk_size=35, chunk_overlap=0)


@pytest.fixture
def complex_text():
    return """
# Chapter 1
Content for Chapter 1, part 1.


Content for Chapter 1, part 2. Lorem ipsum dolor sit amet, consetetur sadipscing elitr.


## Section 1.1
Content for Section 1.1, part 1.


Content for Section 1.1, part 2. Lorem ipsum dolor sit amet, consetetur sadipscing elitr.


### Section 1.1.1
Content for Section 1.1.1


### Section 1.1.2
Content for Section 1.1.2, part 1.


Content for Section 1.1.2, part 2. Lorem ipsum dolor sit amet, consetetur sadipscing elitr.


#### Section 1.1.2.1
Content for Section 1.1.2.1, part 1.


Content for Section 1.1.2.1, part 2. Lorem ipsum dolor sit amet.


### Section 1.1.3
Content for Section 1.1.3.


## Section 1.2
Content for Section 1.2.


#### Section 1.2.0.1
Content for Section 1.2.0.1, part 1.


Content for Section 1.2.0.1, part 2. Lorem ipsum dolor sit amet.


## Section 1.3

## Section 1.4

### Section 1.4.1
Content for Section 1.4.1


###### Section 1.4.1.0.0.1
Content for Section 1.4.1.0.0.1, part 1.


Content for Section 1.4.1.0.0.1, part 2. Lorem ipsum dolor sit amet.


# Chapter 2
Content for Chapter 2.
    """


def test_single_header(node_parser):
    text = "# Header 1\nThis is some content under header 1."
    document = Document(text=text)

    nodes = node_parser.get_nodes_from_node(document)

    assert len(nodes) == 1
    assert nodes[0].text == "# Header 1\nThis is some content under header 1."
    assert nodes[0].metadata[H1] == "Header 1"
    assert nodes[0].metadata[H2] is None
    assert nodes[0].metadata[NAMESPACE] == "test"
    assert nodes[0].metadata[SOURCE] == "test.md"
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id

    assert nodes[0].metadata[INDEX] == 0  # Check the index


def test_multiple_headers(node_parser):
    text = "# Header 1\nContent under header 1.\n## Header 2\nContent under header 2."
    document = Document(text=text)

    nodes = node_parser.get_nodes_from_node(document)

    assert len(nodes) == 2

    # First node, corresponding to Header 1
    assert nodes[0].text == "# Header 1\nContent under header 1."
    assert nodes[0].metadata[H1] == "Header 1"
    assert nodes[0].metadata[H2] is None
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert NodeRelationship.NEXT not in nodes[0].relationships
    assert nodes[0].metadata[INDEX] == 0  # Check the index

    # Second node, corresponding to Header 2
    assert nodes[1].text == "## Header 2\nContent under header 2."
    assert nodes[1].metadata[H1] == "Header 1"  # Parent header
    assert nodes[1].metadata[H2] == "Header 2"  # Current header
    assert nodes[1].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[1].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    assert nodes[1].metadata[INDEX] == 1  # Check the index


def test_nested_headers(node_parser):
    text = (
        "# Header 1\nContent under header 1.\n## Header 2\nContent under header 2.\n### Header 3\nContent under "
        "header 3."
    )
    document = Document(text=text)

    nodes = node_parser.get_nodes_from_node(document)

    assert len(nodes) == 3

    # Node corresponding to Header 1
    assert nodes[0].text == "# Header 1\nContent under header 1."
    assert nodes[0].metadata[H1] == "Header 1"
    assert nodes[0].metadata[H2] is None
    assert nodes[0].metadata[H3] is None
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[0].metadata[INDEX] == 0  # Check the index

    # Node corresponding to Header 2
    assert nodes[1].text == "## Header 2\nContent under header 2."
    assert nodes[1].metadata[H1] == "Header 1"
    assert nodes[1].metadata[H2] == "Header 2"
    assert nodes[1].metadata[H3] is None
    assert nodes[1].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[1].metadata[INDEX] == 1  # Check the index

    # Node corresponding to Header 3
    assert nodes[2].text == "### Header 3\nContent under header 3."
    assert nodes[2].metadata[H1] == "Header 1"
    assert nodes[2].metadata[H2] == "Header 2"
    assert nodes[2].metadata[H3] == "Header 3"
    assert nodes[2].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[2].metadata[INDEX] == 2  # Check the index


def test_relationships(node_parser):
    text = "# Header 1\nContent under header 1.\n## Header 2\nContent under header 2."
    document = Document(text=text)

    nodes = node_parser.get_nodes_from_node(document)

    assert len(nodes) == 2
    assert NodeRelationship.PREVIOUS not in nodes[0].relationships
    assert NodeRelationship.NEXT not in nodes[0].relationships
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[0].metadata[INDEX] == 0  # Check the index

    assert nodes[1].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    assert NodeRelationship.NEXT not in nodes[1].relationships
    assert nodes[1].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[1].metadata[INDEX] == 1  # Check the index


def test_complex_document(node_parser):
    text = """
    # Chapter 1
    Intro content for chapter 1.
    ## Section 1.1
    Content for section 1.1.
    ### Subsection 1.1.1
    Content for subsection 1.1.1.
    ## Section 1.2
    Content for section 1.2.
    # Chapter 2
    Intro content for chapter 2.
    """
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    assert len(nodes) == 5

    # Check Chapter 1
    assert nodes[0].text.startswith("# Chapter 1")
    assert nodes[0].metadata[H1] == "Chapter 1"
    assert nodes[0].metadata[H2] is None
    assert NodeRelationship.PREVIOUS not in nodes[0].relationships
    assert NodeRelationship.NEXT not in nodes[0].relationships
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[0].metadata[INDEX] == 0  # Check the index

    # Check Section 1.1
    assert nodes[1].text.startswith("## Section 1.1")
    assert nodes[1].metadata[H1] == "Chapter 1"
    assert nodes[1].metadata[H2] == "Section 1.1"
    assert nodes[1].metadata[H3] is None
    assert nodes[1].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    assert NodeRelationship.NEXT not in nodes[1].relationships
    assert nodes[1].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[1].metadata[INDEX] == 1  # Check the index

    # Check Subsection 1.1.1
    assert nodes[2].text.startswith("### Subsection 1.1.1")
    assert nodes[2].metadata[H1] == "Chapter 1"
    assert nodes[2].metadata[H2] == "Section 1.1"
    assert nodes[2].metadata[H3] == "Subsection 1.1.1"
    assert nodes[2].relationships[NodeRelationship.PREVIOUS].node_id == nodes[1].node_id
    assert NodeRelationship.NEXT not in nodes[2].relationships
    assert nodes[2].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[2].metadata[INDEX] == 2  # Check the index

    # Check Section 1.2
    assert nodes[3].text.startswith("## Section 1.2")
    assert nodes[3].metadata[H1] == "Chapter 1"
    assert nodes[3].metadata[H2] == "Section 1.2"
    assert nodes[3].metadata[H3] is None
    assert nodes[3].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    assert NodeRelationship.NEXT not in nodes[3].relationships
    assert nodes[3].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[3].metadata[INDEX] == 3  # Check the index

    # Check Chapter 2
    assert nodes[4].text.startswith("# Chapter 2")
    assert nodes[4].metadata[H1] == "Chapter 2"
    assert nodes[4].metadata[H2] is None
    assert NodeRelationship.PREVIOUS not in nodes[4].relationships
    assert NodeRelationship.NEXT not in nodes[4].relationships
    assert nodes[4].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[4].metadata[INDEX] == 4  # Check the index


def test_long_content(node_parser):
    text = "# Chapter 1\n" + "Long content.\n" * 1000
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    assert nodes[0].metadata[H1] == "Chapter 1"
    assert nodes[0].metadata[H2] is None
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[0].relationships[NodeRelationship.NEXT].node_id == nodes[1].node_id
    assert nodes[0].metadata[INDEX] == 0  # Check the index

    assert nodes[1].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    assert nodes[1].metadata[H1] == "Chapter 1"
    assert nodes[1].metadata[H2] is None
    assert nodes[1].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[1].relationships[NodeRelationship.NEXT].node_id == nodes[2].node_id
    assert nodes[1].metadata[INDEX] == 1  # Check the index

    assert nodes[2].relationships[NodeRelationship.PREVIOUS].node_id == nodes[1].node_id
    assert nodes[2].metadata[H1] == "Chapter 1"
    assert nodes[2].metadata[H2] is None
    assert nodes[2].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[2].metadata[INDEX] == 2  # Check the index


def test_no_headers(node_parser):
    text = "This is a document with no headers.\nIt should create one node with no header."
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    assert nodes[0].metadata[H1] is None
    assert nodes[0].metadata[H2] is None
    assert nodes[0].metadata[H3] is None
    assert nodes[0].text == text
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[0].metadata[INDEX] == 0  # Check the index


def test_content_before_headers(node_parser):
    text = "This is a document with content first.\n# Header 1\nContent under header 1."
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    # First node, content before header
    assert nodes[0].metadata[H1] is None
    assert nodes[0].metadata[H2] is None
    assert nodes[0].text == "This is a document with content first."
    assert nodes[0].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[0].metadata[INDEX] == 0  # Check the index

    # Second node, Header 1
    assert nodes[1].metadata[H1] == "Header 1"
    assert nodes[1].metadata[H2] is None
    assert nodes[1].text == "# Header 1\nContent under header 1."
    assert nodes[1].relationships[NodeRelationship.SOURCE].node_id == document.node_id
    assert nodes[1].metadata[INDEX] == 1  # Check the index


def test_correct_relationships_between_sections(node_parser):
    text = """
    # Chapter 1
    Content for Chapter 1.

    ## Section 1.1
    Content for Section 1.1.

    ## Section 1.2
    Content for Section 1.2.

    # Chapter 2
    Content for Chapter 2.
    """
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    assert len(nodes) == 4  # Four nodes expected: Chapter 1, Section 1.1, Section 1.2, Chapter 2

    # Check relationships
    assert nodes[0].metadata[H1] == "Chapter 1"
    assert NodeRelationship.PREVIOUS not in nodes[0].relationships  # First node, no previous
    assert (
        nodes[1].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    )  # Section 1.1 points to Chapter 1
    assert (
        nodes[2].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    )  # Section 1.2 also points to Chapter 1
    assert NodeRelationship.PREVIOUS not in nodes[3].relationships  # Chapter 2 should not link back to Chapter 1


def test_correct_relationship_logic(node_parser):
    text = """
    # Chapter 1
    Content for Chapter 1, part 1.

    Content for Chapter 1, part 2.

    ## Section 1.1
    Content for Section 1.1, part 1.

    Content for Section 1.1, part 2.

    ## Section 1.2
    Content for Section 1.2.

    # Chapter 2
    Content for Chapter 2.
    """
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    # Section 1.1 nodes (part 1 and part 2)
    assert nodes[1].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id  # Links back to Chapter 1
    assert NodeRelationship.NEXT not in nodes[1].relationships

    # Section 1.2 node
    assert nodes[2].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id  # Links back to Chapter 1
    assert NodeRelationship.NEXT not in nodes[2].relationships

    # Chapter 2 node
    assert NodeRelationship.PREVIOUS not in nodes[3].relationships  # No previous relationship
    assert NodeRelationship.NEXT not in nodes[3].relationships


def test_complex_text_correct_node_texts(node_parser_with_chunk_size, complex_text):
    document = Document(text=complex_text)
    nodes = node_parser_with_chunk_size.get_nodes_from_node(document)

    assert len(nodes) == 19
    [
        chapter_1_part_1,
        chapter_1_part_2,
        section_1_1_part_1,
        section_1_1_part_2,
        section_1_1_1,
        section_1_1_2_part_1,
        section_1_1_2_part_2,
        section_1_1_2_1_part_1,
        section_1_1_2_1_part_2,
        section_1_1_3,
        section_1_2,
        section_1_2_0_1_part_1,
        section_1_2_0_1_part_2,
        section_1_3,
        section_1_4,
        section_1_4_1,
        section_1_4_1_0_0_1_part_1,
        section_1_4_1_0_0_1_part_2,
        chapter_2,
    ] = nodes

    assert chapter_1_part_1.text == "# Chapter 1\nContent for Chapter 1, part 1."
    assert (
        chapter_1_part_2.text
        == "Content for Chapter 1, part 2. Lorem ipsum dolor sit amet, consetetur sadipscing elitr."
    )
    assert section_1_1_part_1.text == "## Section 1.1\nContent for Section 1.1, part 1."
    assert (
        section_1_1_part_2.text
        == "Content for Section 1.1, part 2. Lorem ipsum dolor sit amet, consetetur sadipscing elitr."
    )
    assert section_1_1_1.text == "### Section 1.1.1\nContent for Section 1.1.1"
    assert section_1_1_2_part_1.text == "### Section 1.1.2\nContent for Section 1.1.2, part 1."
    assert (
        section_1_1_2_part_2.text
        == "Content for Section 1.1.2, part 2. Lorem ipsum dolor sit amet, consetetur sadipscing elitr."
    )
    assert section_1_1_2_1_part_1.text == "#### Section 1.1.2.1\nContent for Section 1.1.2.1, part 1."
    assert section_1_1_2_1_part_2.text == "Content for Section 1.1.2.1, part 2. Lorem ipsum dolor sit amet."
    assert section_1_1_3.text == "### Section 1.1.3\nContent for Section 1.1.3."
    assert section_1_2.text == "## Section 1.2\nContent for Section 1.2."
    assert section_1_2_0_1_part_1.text == "#### Section 1.2.0.1\nContent for Section 1.2.0.1, part 1."
    assert section_1_2_0_1_part_2.text == "Content for Section 1.2.0.1, part 2. Lorem ipsum dolor sit amet."
    assert section_1_3.text == "## Section 1.3"
    assert section_1_4.text == "## Section 1.4"
    assert section_1_4_1.text == "### Section 1.4.1\nContent for Section 1.4.1"
    assert section_1_4_1_0_0_1_part_1.text == "###### Section 1.4.1.0.0.1\nContent for Section 1.4.1.0.0.1, part 1."
    assert section_1_4_1_0_0_1_part_2.text == "Content for Section 1.4.1.0.0.1, part 2. Lorem ipsum dolor sit amet."
    assert chapter_2.text == "# Chapter 2\nContent for Chapter 2."


def test_complex_text_correct_node_header_meta(node_parser_with_chunk_size, complex_text):
    document = Document(text=complex_text)
    nodes = node_parser_with_chunk_size.get_nodes_from_node(document)

    assert len(nodes) == 19
    [
        chapter_1_part_1,
        chapter_1_part_2,
        section_1_1_part_1,
        section_1_1_part_2,
        section_1_1_1,
        section_1_1_2_part_1,
        section_1_1_2_part_2,
        section_1_1_2_1_part_1,
        section_1_1_2_1_part_2,
        section_1_1_3,
        section_1_2,
        section_1_2_0_1_part_1,
        section_1_2_0_1_part_2,
        section_1_3,
        section_1_4,
        section_1_4_1,
        section_1_4_1_0_0_1_part_1,
        section_1_4_1_0_0_1_part_2,
        chapter_2,
    ] = nodes

    assert chapter_1_part_1.metadata[H1] == "Chapter 1"
    assert all([chapter_1_part_1.metadata[h] is None for h in [H2, H3, H4, H5, H6]])
    assert chapter_1_part_2.metadata[H1] == "Chapter 1"
    assert all([chapter_1_part_2.metadata[h] is None for h in [H2, H3, H4, H5, H6]])
    assert section_1_1_part_1.metadata[H1] == "Chapter 1"
    assert section_1_1_part_1.metadata[H2] == "Section 1.1"
    assert all([section_1_1_part_1.metadata[h] is None for h in [H3, H4, H5, H6]])
    assert section_1_1_part_2.metadata[H1] == "Chapter 1"
    assert section_1_1_part_2.metadata[H2] == "Section 1.1"
    assert all([section_1_1_part_2.metadata[h] is None for h in [H3, H4, H5, H6]])
    assert section_1_1_1.metadata[H1] == "Chapter 1"
    assert section_1_1_1.metadata[H2] == "Section 1.1"
    assert section_1_1_1.metadata[H3] == "Section 1.1.1"
    assert all([section_1_1_1.metadata[h] is None for h in [H4, H5, H6]])
    assert section_1_1_2_part_1.metadata[H1] == "Chapter 1"
    assert section_1_1_2_part_1.metadata[H2] == "Section 1.1"
    assert section_1_1_2_part_1.metadata[H3] == "Section 1.1.2"
    assert all([section_1_1_2_part_1.metadata[h] is None for h in [H4, H5, H6]])
    assert section_1_1_2_part_2.metadata[H1] == "Chapter 1"
    assert section_1_1_2_part_2.metadata[H2] == "Section 1.1"
    assert section_1_1_2_part_2.metadata[H3] == "Section 1.1.2"
    assert all([section_1_1_2_part_2.metadata[h] is None for h in [H4, H5, H6]])
    assert section_1_1_2_1_part_1.metadata[H1] == "Chapter 1"
    assert section_1_1_2_1_part_1.metadata[H2] == "Section 1.1"
    assert section_1_1_2_1_part_1.metadata[H3] == "Section 1.1.2"
    assert section_1_1_2_1_part_1.metadata[H4] == "Section 1.1.2.1"
    assert all([section_1_1_2_1_part_1.metadata[h] is None for h in [H5, H6]])
    assert section_1_1_2_1_part_2.metadata[H1] == "Chapter 1"
    assert section_1_1_2_1_part_2.metadata[H2] == "Section 1.1"
    assert section_1_1_2_1_part_2.metadata[H3] == "Section 1.1.2"
    assert section_1_1_2_1_part_2.metadata[H4] == "Section 1.1.2.1"
    assert all([section_1_1_2_1_part_2.metadata[h] is None for h in [H5, H6]])
    assert section_1_1_3.metadata[H1] == "Chapter 1"
    assert section_1_1_3.metadata[H2] == "Section 1.1"
    assert section_1_1_3.metadata[H3] == "Section 1.1.3"
    assert all([section_1_1_3.metadata[h] is None for h in [H4, H5, H6]])
    assert section_1_2.metadata[H1] == "Chapter 1"
    assert section_1_2.metadata[H2] == "Section 1.2"
    assert all([section_1_2.metadata[h] is None for h in [H3, H4, H5, H6]])
    assert section_1_2_0_1_part_1.metadata[H1] == "Chapter 1"
    assert section_1_2_0_1_part_1.metadata[H2] == "Section 1.2"
    assert section_1_2_0_1_part_1.metadata[H4] == "Section 1.2.0.1"
    assert all([section_1_2_0_1_part_1.metadata[h] is None for h in [H3, H5, H6]])
    assert section_1_2_0_1_part_2.metadata[H1] == "Chapter 1"
    assert section_1_2_0_1_part_2.metadata[H2] == "Section 1.2"
    assert section_1_2_0_1_part_2.metadata[H4] == "Section 1.2.0.1"
    assert all([section_1_2_0_1_part_2.metadata[h] is None for h in [H3, H5, H6]])
    assert section_1_3.metadata[H1] == "Chapter 1"
    assert section_1_3.metadata[H2] == "Section 1.3"
    assert all([section_1_3.metadata[h] is None for h in [H3, H4, H5, H6]])
    assert section_1_4.metadata[H1] == "Chapter 1"
    assert section_1_4.metadata[H2] == "Section 1.4"
    assert all([section_1_4.metadata[h] is None for h in [H3, H4, H5, H6]])
    assert section_1_4_1.metadata[H1] == "Chapter 1"
    assert section_1_4_1.metadata[H2] == "Section 1.4"
    assert section_1_4_1.metadata[H3] == "Section 1.4.1"
    assert all([section_1_4_1.metadata[h] is None for h in [H4, H5, H6]])
    assert section_1_4_1_0_0_1_part_1.metadata[H1] == "Chapter 1"
    assert section_1_4_1_0_0_1_part_1.metadata[H2] == "Section 1.4"
    assert section_1_4_1_0_0_1_part_1.metadata[H3] == "Section 1.4.1"
    assert section_1_4_1_0_0_1_part_1.metadata[H6] == "Section 1.4.1.0.0.1"
    assert all([section_1_4_1_0_0_1_part_1.metadata[h] is None for h in [H4, H5]])
    assert section_1_4_1_0_0_1_part_2.metadata[H1] == "Chapter 1"
    assert section_1_4_1_0_0_1_part_2.metadata[H2] == "Section 1.4"
    assert section_1_4_1_0_0_1_part_2.metadata[H3] == "Section 1.4.1"
    assert section_1_4_1_0_0_1_part_2.metadata[H6] == "Section 1.4.1.0.0.1"
    assert all([section_1_4_1_0_0_1_part_2.metadata[h] is None for h in [H4, H5]])
    assert chapter_2.metadata[H1] == "Chapter 2"
    assert all([chapter_2.metadata[h] is None for h in [H2, H3, H4, H5, H6]])


def test_complex_text_correct_node_prev_and_next(node_parser_with_chunk_size, complex_text):
    document = Document(text=complex_text)
    nodes = node_parser_with_chunk_size.get_nodes_from_node(document)

    assert len(nodes) == 19
    [
        chapter_1_part_1,
        chapter_1_part_2,
        section_1_1_part_1,
        section_1_1_part_2,
        section_1_1_1,
        section_1_1_2_part_1,
        section_1_1_2_part_2,
        section_1_1_2_1_part_1,
        section_1_1_2_1_part_2,
        section_1_1_3,
        section_1_2,
        section_1_2_0_1_part_1,
        section_1_2_0_1_part_2,
        section_1_3,
        section_1_4,
        section_1_4_1,
        section_1_4_1_0_0_1_part_1,
        section_1_4_1_0_0_1_part_2,
        chapter_2,
    ] = nodes

    # write helper that check is one node has a next relationship to another node
    def has_next(node, next_node):
        return node.relationships[NodeRelationship.NEXT].node_id == next_node.node_id

    def has_no_next(node):
        return NodeRelationship.NEXT not in node.relationships

    def has_prev(node, prev_node):
        return node.relationships[NodeRelationship.PREVIOUS].node_id == prev_node.node_id

    def has_no_prev(node):
        return NodeRelationship.PREVIOUS not in node.relationships

    assert has_no_prev(chapter_1_part_1)
    assert has_next(chapter_1_part_1, chapter_1_part_2)
    assert has_prev(chapter_1_part_2, chapter_1_part_1)
    assert has_no_next(chapter_1_part_2)
    assert has_prev(section_1_1_part_1, chapter_1_part_2)
    assert has_next(section_1_1_part_1, section_1_1_part_2)
    assert has_prev(section_1_1_part_2, section_1_1_part_1)
    assert has_no_next(section_1_1_part_2)
    assert has_prev(section_1_1_1, section_1_1_part_2)
    assert has_no_next(section_1_1_1)
    assert has_prev(section_1_1_2_part_1, section_1_1_part_2)
    assert has_next(section_1_1_2_part_1, section_1_1_2_part_2)
    assert has_prev(section_1_1_2_part_2, section_1_1_2_part_1)
    assert has_no_next(section_1_1_2_part_2)
    assert has_prev(section_1_1_2_1_part_1, section_1_1_2_part_2)
    assert has_next(section_1_1_2_1_part_1, section_1_1_2_1_part_2)
    assert has_prev(section_1_1_2_1_part_2, section_1_1_2_1_part_1)
    assert has_no_next(section_1_1_2_1_part_2)
    assert has_prev(section_1_1_3, section_1_1_part_2)
    assert has_no_next(section_1_1_3)
    assert has_prev(section_1_2, chapter_1_part_2)
    assert has_no_next(section_1_2)
    assert has_prev(section_1_2_0_1_part_1, section_1_2)
    assert has_next(section_1_2_0_1_part_1, section_1_2_0_1_part_2)
    assert has_prev(section_1_2_0_1_part_2, section_1_2_0_1_part_1)
    assert has_no_next(section_1_2_0_1_part_2)
    assert has_prev(section_1_3, chapter_1_part_2)
    assert has_no_next(section_1_3)
    assert has_prev(section_1_4, chapter_1_part_2)
    assert has_no_next(section_1_4)
    assert has_prev(section_1_4_1, section_1_4)
    assert has_no_next(section_1_4_1)
    assert has_prev(section_1_4_1_0_0_1_part_1, section_1_4_1)
    assert has_next(section_1_4_1_0_0_1_part_1, section_1_4_1_0_0_1_part_2)
    assert has_prev(section_1_4_1_0_0_1_part_2, section_1_4_1_0_0_1_part_1)
    assert has_no_next(section_1_4_1_0_0_1_part_2)
    assert has_no_prev(chapter_2)
    assert has_no_next(chapter_2)


def test_complex_text_correct_node_lines_meta(node_parser_with_chunk_size, complex_text):
    document = Document(text=complex_text)
    nodes = node_parser_with_chunk_size.get_nodes_from_node(document)

    assert len(nodes) == 19
    [
        chapter_1_part_1,
        chapter_1_part_2,
        section_1_1_part_1,
        section_1_1_part_2,
        section_1_1_1,
        section_1_1_2_part_1,
        section_1_1_2_part_2,
        section_1_1_2_1_part_1,
        section_1_1_2_1_part_2,
        section_1_1_3,
        section_1_2,
        section_1_2_0_1_part_1,
        section_1_2_0_1_part_2,
        section_1_3,
        section_1_4,
        section_1_4_1,
        section_1_4_1_0_0_1_part_1,
        section_1_4_1_0_0_1_part_2,
        chapter_2,
    ] = nodes

    assert chapter_1_part_1.metadata["section_start_line"] == 0
    assert chapter_1_part_1.metadata["section_end_line"] == 6
    assert chapter_1_part_2.metadata["section_start_line"] == 0
    assert chapter_1_part_2.metadata["section_end_line"] == 6
    assert section_1_1_part_1.metadata["section_start_line"] == 7
    assert section_1_1_part_1.metadata["section_end_line"] == 13
    assert section_1_1_part_2.metadata["section_start_line"] == 7
    assert section_1_1_part_2.metadata["section_end_line"] == 13
    assert section_1_1_1.metadata["section_start_line"] == 14
    assert section_1_1_1.metadata["section_end_line"] == 17
    assert section_1_1_2_part_1.metadata["section_start_line"] == 18
    assert section_1_1_2_part_1.metadata["section_end_line"] == 24
    assert section_1_1_2_part_2.metadata["section_start_line"] == 18
    assert section_1_1_2_part_2.metadata["section_end_line"] == 24
    assert section_1_1_2_1_part_1.metadata["section_start_line"] == 25
    assert section_1_1_2_1_part_1.metadata["section_end_line"] == 31
    assert section_1_1_2_1_part_2.metadata["section_start_line"] == 25
    assert section_1_1_2_1_part_2.metadata["section_end_line"] == 31
    assert section_1_1_3.metadata["section_start_line"] == 32
    assert section_1_1_3.metadata["section_end_line"] == 35
    assert section_1_2.metadata["section_start_line"] == 36
    assert section_1_2.metadata["section_end_line"] == 39
    assert section_1_2_0_1_part_1.metadata["section_start_line"] == 40
    assert section_1_2_0_1_part_1.metadata["section_end_line"] == 46
    assert section_1_2_0_1_part_2.metadata["section_start_line"] == 40
    assert section_1_2_0_1_part_2.metadata["section_end_line"] == 46
    assert section_1_3.metadata["section_start_line"] == 47
    assert section_1_3.metadata["section_end_line"] == 48
    assert section_1_4.metadata["section_start_line"] == 49
    assert section_1_4.metadata["section_end_line"] == 50
    assert section_1_4_1.metadata["section_start_line"] == 51
    assert section_1_4_1.metadata["section_end_line"] == 54
    assert section_1_4_1_0_0_1_part_1.metadata["section_start_line"] == 55
    assert section_1_4_1_0_0_1_part_1.metadata["section_end_line"] == 61
    assert section_1_4_1_0_0_1_part_2.metadata["section_start_line"] == 55
    assert section_1_4_1_0_0_1_part_2.metadata["section_end_line"] == 61
    assert chapter_2.metadata["section_start_line"] == 62
    assert chapter_2.metadata["section_end_line"] == 63


def test_complex_text_correct_node_index_meta(node_parser_with_chunk_size, complex_text):
    document = Document(text=complex_text)
    nodes = node_parser_with_chunk_size.get_nodes_from_node(document)

    for i, node in enumerate(nodes):
        assert node.metadata[INDEX] == i


def test_page_numbers_are_set_correctly(node_parser):
    text = (
        """# Page 1
    Content on page 1.
    """
        + f"{PAGE_BREAK}\n"
        + """
    # Page 2
    Content on page 2.
    """
        + f"{PAGE_BREAK}\n"
        + """
    # Page 3
    Content on page 3."""
    )
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)
    # Should have 3 nodes, each with correct page number
    assert nodes[0].metadata["page"] == 1
    assert nodes[1].metadata["page"] == 2
    assert nodes[2].metadata["page"] == 3
    assert nodes[0].text.startswith("# Page 1")
    assert nodes[1].text.startswith("# Page 2")
    assert nodes[2].text.startswith("# Page 3")


def test_table_extraction(node_parser):
    text = """# Section
    Some intro text.
    <table>| Cell 1 | Cell 2 |
|--------|--------|
| Data 1 | Data 2 |</table>
    Some outro text."""
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)
    # Should extract the table as a separate node
    table_nodes = [n for n in nodes if "Cell 1" in n.text and "Cell 2" in n.text]
    assert len(table_nodes) == 1
    assert table_nodes[0].text.strip().startswith("| Cell 1")
    # The other nodes should contain the intro and outro text
    intro_nodes = [n for n in nodes if "Some intro text." in n.text]
    outro_nodes = [n for n in nodes if "Some outro text." in n.text]
    assert intro_nodes
    assert outro_nodes


def test_figure_extraction(node_parser):
    text = """# Section
    Some intro text.
    <figure>Figure content here</figure>
    Some outro text."""
    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)
    # Should extract the figure as a separate node
    figure_nodes = [n for n in nodes if "Figure content here" in n.text]
    assert len(figure_nodes) == 1
    assert figure_nodes[0].text.strip().startswith("Figure content here")
    # The other nodes should contain the intro and outro text
    intro_nodes = [n for n in nodes if "Some intro text." in n.text]
    outro_nodes = [n for n in nodes if "Some outro text." in n.text]
    assert intro_nodes
    assert outro_nodes


def test_large_table_splitting():
    """Test that large tables are split into multiple chunks with headers preserved."""
    metadata = {
        NAMESPACE: "test",
        SOURCE: "test.md",
        CREATED_AT: int(time()),
        UPDATED_AT: int(time()),
        INSERTED_AT: int(time()),
    }
    # Use a small chunk size to force splitting
    node_parser = MarkdownStructuralNodeParser(metadata=metadata, chunk_size=50, chunk_overlap=0)

    # Create a markdown table with header and many rows to exceed chunk size
    table_rows = ["| Column 1 | Column 2 | Column 3 |", "|----------|----------|----------|"]
    for i in range(20):
        table_rows.append(f"| Data {i}A | Data {i}B | Data {i}C |")

    table_text = "<table>" + "\n".join(table_rows) + "</table>"

    text = f"""# Section with Table
Some intro text.
{table_text}
Some outro text."""

    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    # Find all table nodes
    table_nodes = [n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "table"]

    # Should have multiple table chunks
    assert len(table_nodes) > 1, f"Expected multiple table chunks, got {len(table_nodes)}"

    # Each chunk should contain the header
    for table_node in table_nodes:
        assert "Column 1" in table_node.text, f"Header missing in chunk: {table_node.text}"

    # All chunks should have the same metadata (except index)
    first_table = table_nodes[0]
    for table_node in table_nodes[1:]:
        assert table_node.metadata[H1] == first_table.metadata[H1]
        assert table_node.metadata[NODE_CONTENT_TYPE] == "table"


def test_small_table_not_split(node_parser):
    """Test that small tables are kept intact."""
    table_text = """| Col1 | Col2 |
|------|------|
| A    | B    |
| C    | D    |"""

    text = f"""# Section
<table>{table_text}</table>"""

    document = Document(text=text)
    nodes = node_parser.get_nodes_from_node(document)

    # Find table nodes
    table_nodes = [n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "table"]

    # Should have only one table node since it's small
    assert len(table_nodes) == 1
    assert "Col1" in table_nodes[0].text
    assert "Col2" in table_nodes[0].text


def test_invalid_table_html_handled_gracefully(node_parser):
    """Test that invalid table HTML (without proper <td>/<tr> elements) doesn't crash.

    Regression test for ValueError: No tables found matching pattern '.+'
    when pd.read_html() is called on HTML that doesn't contain valid table structure.
    """
    # Table tag without proper structure - pd.read_html will raise ValueError
    text = """# Section
<table>This is not a valid table structure</table>
Some following text."""

    document = Document(text=text)
    # Should not raise an exception
    nodes = node_parser.get_nodes_from_node(document)

    # Invalid table content is preserved as TABLE type (backward compatible)
    table_nodes = [n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "table"]
    assert len(table_nodes) == 1
    assert "This is not a valid table structure" in table_nodes[0].text


def test_empty_table_handled_gracefully(node_parser):
    """Test that empty table elements don't crash and are skipped."""
    text = """# Section
<table></table>
Some following text."""

    document = Document(text=text)
    # Should not raise an exception
    nodes = node_parser.get_nodes_from_node(document)

    # Empty tables are skipped entirely - no table nodes should be created
    table_nodes = [n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "table"]
    assert len(table_nodes) == 0

    # The other content should still be present
    text_nodes = [n for n in nodes if "Some following text" in n.text]
    assert len(text_nodes) == 1


def _parser_with_embedding_ceiling(max_embedding_tokens: int) -> MarkdownStructuralNodeParser:
    metadata = {
        NAMESPACE: "test",
        SOURCE: "test.md",
        CREATED_AT: int(time()),
        UPDATED_AT: int(time()),
        INSERTED_AT: int(time()),
    }
    return MarkdownStructuralNodeParser(
        metadata=metadata, chunk_size=512, chunk_overlap=0, max_embedding_tokens=max_embedding_tokens
    )


def test_unparseable_table_is_capped_at_the_embedding_ceiling():
    """The table-parse fallback used to emit the whole table as one unbounded node."""
    parser = _parser_with_embedding_ceiling(max_embedding_tokens=200)
    digits = " ".join(str(number) for number in range(4000))

    nodes = parser.get_nodes_from_node(Document(text=f"# Section\n<table>{digits}</table>"))

    table_nodes = [n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "table"]
    assert len(table_nodes) > 1
    # _count_tokens without an llm_config estimates 4 characters per token.
    assert all(len(n.text) // 4 <= int(200 * 0.85) for n in table_nodes)


def test_figure_description_is_capped_at_the_embedding_ceiling():
    """The figure branch had no size check at all; vision-LLM descriptions are unbounded."""
    parser = _parser_with_embedding_ceiling(max_embedding_tokens=200)
    description = " ".join(f"word{i}" for i in range(4000))

    nodes = parser.get_nodes_from_node(Document(text=f"# Section\n<figure>{description}</figure>"))

    figure_nodes = [n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "figure"]
    assert len(figure_nodes) > 1
    assert all(len(n.text) // 4 <= int(200 * 0.85) for n in figure_nodes)


def test_ceiling_leaves_small_tables_and_figures_alone():
    parser = _parser_with_embedding_ceiling(max_embedding_tokens=8192)
    text = """# Section
<table>| Col1 | Col2 |
|------|------|
| A    | B    |</table>
<figure>A short figure description</figure>"""

    nodes = parser.get_nodes_from_node(Document(text=text))

    assert len([n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "table"]) == 1
    assert len([n for n in nodes if n.metadata.get(NODE_CONTENT_TYPE) == "figure"]) == 1
