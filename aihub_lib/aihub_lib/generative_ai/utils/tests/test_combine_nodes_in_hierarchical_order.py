import unittest
from unittest.mock import MagicMock

from llama_index.core.base.llms.types import MessageRole
from llama_index.core.schema import TextNode

from aihub_lib.generative_ai.utils.combine_nodes_in_hierarchical_order import combine_nodes_in_hierarchical_order
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.semantic.retriever import Document
from aihub_lib.persistence.rag.vectors.node_metadata import (
    H1, H2, H3,
    HEADING_LEVEL,
    NAMESPACE,
    NODE_TYPE_CONTENT,
    NODE_TYPE_SUMMARY,
    SECTION_START_LINE,
    SOURCE,
    TYPE,
)


class TestCombineNodesInHierarchicalOrder(unittest.TestCase):

    def setUp(self):
        self.locale_handler = MagicMock(spec=LocaleHandler)
        self.locale_handler.return_value = "This is the context: {context_str}"
        self.locale_handler.locale = "en"
        extract_mock = MagicMock()
        extract_mock.format.return_value = "This is the context: {context_str}"
        self.locale_handler.extract.return_value = extract_mock

    def convert_to_document(self, text_node):
        """Helper to convert TextNode to Document"""
        return Document(
            id=text_node.node_id,  # Use the node_id as the Document's id
            content=text_node.text,
            metadata=text_node.metadata,
            score=0.9  # Add a default score
        )

    def test_empty_nodes(self):
        """Test with empty nodes list"""
        result = combine_nodes_in_hierarchical_order([], self.locale_handler)

        self.assertEqual(result.role, MessageRole.SYSTEM)
        self.assertEqual(result.content, "This is the context: ")

    def test_basic_content_no_summaries(self):
        """Test with only content nodes, no summaries"""
        nodes = [
            TextNode(
                text="This is content 1",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    SECTION_START_LINE: 10,
                },
                id_="content1"
            ),
            TextNode(
                text="This is content 2",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    SECTION_START_LINE: 20,
                },
                id_="content2"
            )
        ]

        documents = [self.convert_to_document(node) for node in nodes]
        result = combine_nodes_in_hierarchical_order(documents, self.locale_handler)

        self.assertIn("This is content 1", result.content)
        self.assertIn("This is content 2", result.content)
        self.assertIn("<DOCUMENT source='test.pdf' namespace='test_namespace' type='content'>", result.content)
        self.assertIn("</DOCUMENT>", result.content)
        self.assertIn("<remaining_content>", result.content)

        content1_pos = result.content.find("This is content 1")
        content2_pos = result.content.find("This is content 2")
        self.assertLess(content1_pos, content2_pos)

    def test_single_level_hierarchy(self):
        """Test with H1 summaries and related content"""
        nodes = [
            # H1 Summary
            TextNode(
                text="Introduction Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Introduction",
                    SECTION_START_LINE: 0,
                },
                id_="intro_summary"
            ),
            # Content under Introduction
            TextNode(
                text="This is the introduction content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Introduction",
                    SECTION_START_LINE: 0,
                },
                id_="intro_content"
            ),
            # H1 Summary
            TextNode(
                text="Conclusion Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Conclusion",
                    SECTION_START_LINE: 100,
                },
                id_="conclusion_summary"
            ),
            # Content under Conclusion
            TextNode(
                text="This is the conclusion content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Conclusion",
                    SECTION_START_LINE: 100,
                },
                id_="conclusion_content"
            ),
        ]

        documents = [self.convert_to_document(node) for node in nodes]
        result = combine_nodes_in_hierarchical_order(documents, self.locale_handler)

        # Check if summaries and contents are present
        self.assertIn("<h1>Section Summary</h1>", result.content)
        self.assertIn("<summary>Introduction Summary</summary>", result.content)
        self.assertIn("This is the introduction content.", result.content)

        self.assertIn("<summary>Conclusion Summary</summary>", result.content)
        self.assertIn("This is the conclusion content.", result.content)

        # Introduction should come before conclusion
        intro_pos = result.content.find("Introduction Summary")
        conclusion_pos = result.content.find("Conclusion Summary")
        self.assertLess(intro_pos, conclusion_pos)

    def test_multi_level_hierarchy(self):
        nodes = [
            TextNode(
                text="Chapter 1 Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Chapter 1",
                    SECTION_START_LINE: 0,
                },
                id_="chapter1_summary"
            ),
            TextNode(
                text="Section 1.1 Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 2,
                    H1: "Chapter 1",
                    H2: "Section 1.1",
                    SECTION_START_LINE: 10,
                },
                id_="section1.1_summary"
            ),
            TextNode(
                text="This is section 1.1 content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Chapter 1",
                    H2: "Section 1.1",
                    SECTION_START_LINE: 10,
                },
                id_="section1.1_content"
            ),
            TextNode(
                text="Subsection 1.1.1 Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 3,
                    H1: "Chapter 1",
                    H2: "Section 1.1",
                    H3: "Subsection 1.1.1",
                    SECTION_START_LINE: 15,
                },
                id_="subsection1.1.1_summary"
            ),
            TextNode(
                text="This is subsection 1.1.1 content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Chapter 1",
                    H2: "Section 1.1",
                    H3: "Subsection 1.1.1",
                    SECTION_START_LINE: 15,
                },
                id_="section1.1.1_content"
            ),
            TextNode(
                text="Section 1.2 Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 2,
                    H1: "Chapter 1",
                    H2: "Section 1.2",
                    SECTION_START_LINE: 50,
                },
                id_="section1.2_summary"
            ),
            TextNode(
                text="This is section 1.2 content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Chapter 1",
                    H2: "Section 1.2",
                    SECTION_START_LINE: 50,
                },
                id_="section1.2_content"
            ),
        ]

        documents = [self.convert_to_document(node) for node in nodes]
        result = combine_nodes_in_hierarchical_order(documents, self.locale_handler)
        print(result)

        self.assertIn("<summary>Chapter 1 Summary</summary>", result.content)
        self.assertIn("<summary>Section 1.1 Summary</summary>", result.content)
        self.assertIn("<summary>Subsection 1.1.1 Summary</summary>", result.content)
        self.assertIn("<summary>Section 1.2 Summary</summary>", result.content)

        self.assertIn("This is section 1.1 content.", result.content)
        self.assertIn("This is subsection 1.1.1 content.", result.content)
        self.assertIn("This is section 1.2 content.", result.content)

        chapter_pos = result.content.find("Chapter 1 Summary")
        section1_pos = result.content.find("Section 1.1 Summary")
        subsection_pos = result.content.find("Subsection 1.1.1 Summary")
        section2_pos = result.content.find("Section 1.2 Summary")

        self.assertLess(chapter_pos, section1_pos, "Chapter 1 summary should appear before Section 1.1 summary")
        self.assertLess(section1_pos, section2_pos, "Section 1.1 summary should appear before Section 1.2 summary")

    def test_multiple_documents(self):
        """Test with nodes from multiple documents"""
        doc1_nodes = [
            TextNode(
                text="Document 1 Summary",
                metadata={
                    SOURCE: "doc1.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Document 1",
                    SECTION_START_LINE: 0,
                },
                id_="doc1_summary"
            ),
            TextNode(
                text="This is document 1 content.",
                metadata={
                    SOURCE: "doc1.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Document 1",
                    SECTION_START_LINE: 0,
                },
                id_="doc1_content"
            ),
        ]

        doc2_nodes = [
            TextNode(
                text="Document 2 Summary",
                metadata={
                    SOURCE: "doc2.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Document 2",
                    SECTION_START_LINE: 0,
                },
                id_="doc2_summary"
            ),
            TextNode(
                text="This is document 2 content.",
                metadata={
                    SOURCE: "doc2.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Document 2",
                    SECTION_START_LINE: 0,
                },
                id_="doc2_content"
            ),
        ]

        all_nodes = doc1_nodes + doc2_nodes
        documents = [self.convert_to_document(node) for node in all_nodes]
        result = combine_nodes_in_hierarchical_order(documents, self.locale_handler)

        self.assertIn("<DOCUMENT source='doc1.pdf'", result.content)
        self.assertIn("<DOCUMENT source='doc2.pdf'", result.content)

        self.assertIn("Document 1 Summary", result.content)
        self.assertIn("This is document 1 content.", result.content)
        self.assertIn("Document 2 Summary", result.content)
        self.assertIn("This is document 2 content.", result.content)

        self.assertIn("</DOCUMENT>\n\n---\n", result.content)

    def test_document_level_summary(self):
        """Test with document-level summary (HEADING_LEVEL = 0)"""
        nodes = [
            TextNode(
                text="Overall Document Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 0,
                    SECTION_START_LINE: 0,
                },
                id_="doc_summary"
            ),
            TextNode(
                text="Chapter 1 Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Chapter 1",
                    SECTION_START_LINE: 10,
                },
                id_="chapter1_summary"
            ),
            TextNode(
                text="This is chapter 1 content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Chapter 1",
                    SECTION_START_LINE: 10,
                },
                id_="chapter1_content"
            ),
        ]

        documents = [self.convert_to_document(node) for node in nodes]
        result = combine_nodes_in_hierarchical_order(documents, self.locale_handler)

        self.assertIn("<summary>Overall Document Summary</summary>", result.content)
        self.assertIn("<summary>Chapter 1 Summary</summary>", result.content)

        doc_summary_pos = result.content.find("Overall Document Summary")
        chapter_summary_pos = result.content.find("Chapter 1 Summary")
        self.assertLess(doc_summary_pos, chapter_summary_pos)

    def test_content_without_matching_summary(self):
        """Test with content that doesn't have a matching summary"""
        nodes = [
            TextNode(
                text="Introduction Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Introduction",
                    SECTION_START_LINE: 0,
                },
                id_="intro_summary"
            ),
            TextNode(
                text="This is introduction content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Introduction",
                    SECTION_START_LINE: 0,
                },
                id_="intro_content"
            ),
            TextNode(
                text="This is orphaned content without a summary.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    SECTION_START_LINE: 50,
                },
                id_="orphaned_content"
            ),
        ]

        documents = [self.convert_to_document(node) for node in nodes]
        result = combine_nodes_in_hierarchical_order(documents, self.locale_handler)

        self.assertIn("This is introduction content.", result.content)
        self.assertIn("This is orphaned content without a summary.", result.content)

        self.assertIn("<remaining_content>", result.content)

    def test_summaries_without_matching_content(self):
        """Test with summaries that don't have matching content"""
        nodes = [
            TextNode(
                text="Introduction Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Introduction",
                    SECTION_START_LINE: 0,
                },
                id_="intro_summary"
            ),
            TextNode(
                text="This is introduction content.",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_CONTENT,
                    H1: "Introduction",
                    SECTION_START_LINE: 0,
                },
                id_="intro_content"
            ),
            TextNode(
                text="Conclusion Summary",
                metadata={
                    SOURCE: "test.pdf",
                    NAMESPACE: "test_namespace",
                    TYPE: NODE_TYPE_SUMMARY,
                    HEADING_LEVEL: 1,
                    H1: "Conclusion",
                    SECTION_START_LINE: 100,
                },
                id_="conclusion_summary"
            ),
        ]

        documents = [self.convert_to_document(node) for node in nodes]
        result = combine_nodes_in_hierarchical_order(documents, self.locale_handler)

        self.assertIn("<summary>Introduction Summary</summary>", result.content)
        self.assertIn("<summary>Conclusion Summary</summary>", result.content)

        self.assertIn("This is introduction content.", result.content)

        conclusion_pos = result.content.find("Conclusion Summary")
        self.assertGreater(conclusion_pos, 0)


if __name__ == "__main__":
    unittest.main()