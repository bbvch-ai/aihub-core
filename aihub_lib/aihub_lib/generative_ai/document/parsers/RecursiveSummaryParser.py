from typing import Any

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.rag.vectors.node_metadata import (
    HEADING_LEVEL,
    INDEX,
    LANGUAGE,
    NODE_LANGUAGE_ENGLISH,
    NODE_TYPE_SUMMARY,
    SECTION_START_LINE,
    TYPE,
)


class LLMSummarizer:
    def __init__(self, llm: LLM, t: LocaleHandler):
        self._llm: LLM = llm
        prompt_str: str = t("lib.prompt.summarizer.summarize")
        self._summarize_prompt_template: PromptTemplate = PromptTemplate(prompt_str)

    def summarize(self, text: str) -> str:
        if not text or not text.strip():
            return ""
        response: str = self._llm.predict(self._summarize_prompt_template, text=text)
        return response.strip()


class RecursiveNodeSummarizer:
    def __init__(
        self,
        llm: LLM,
        min_summarization_length: int = 250,
    ):
        self._llm = llm
        self.min_summarization_length = min_summarization_length
        self.node_id_to_node = {}

    def summarize_nodes(self, nodes: list[TextNode]) -> list[TextNode]:
        if not nodes:
            return []

        locale = nodes[0].metadata.get(LANGUAGE, NODE_LANGUAGE_ENGLISH)
        locale_handler = LocaleHandler(locale=locale)
        llm_summarizer: LLMSummarizer = LLMSummarizer(llm=self._llm, t=locale_handler)

        self.node_id_to_node = {node.node_id: node for node in nodes}
        grouped_nodes = self._group_nodes_by_level(nodes)
        for level_nodes_list in grouped_nodes.values():
            level_nodes_list.sort(key=lambda n: n.metadata.get(SECTION_START_LINE, float("inf")))

        max_level: int = max(grouped_nodes.keys()) if grouped_nodes else -1

        all_generated_summaries: list[TextNode] = []

        for level in range(max_level, -1, -1):
            original_nodes_at_this_level: list[TextNode] = grouped_nodes.get(level, [])

            child_summaries_for_this_level: list[TextNode] = [
                s_node for s_node in all_generated_summaries if s_node.metadata.get(HEADING_LEVEL) == level + 1
            ]

            summarized_nodes_at_this_level: list[TextNode] = self._summarize_level(
                original_nodes_at_this_level, child_summaries_for_this_level, level, llm_summarizer
            )

            for i, s_node in enumerate(summarized_nodes_at_this_level):
                if i > 0:
                    prev_node_id = summarized_nodes_at_this_level[i - 1].node_id
                    s_node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=prev_node_id)
                if i < len(summarized_nodes_at_this_level) - 1:
                    next_node_id = summarized_nodes_at_this_level[i + 1].node_id
                    s_node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=next_node_id)

            all_generated_summaries.extend(summarized_nodes_at_this_level)

        for s_node in all_generated_summaries:
            self.node_id_to_node[s_node.node_id] = s_node

        return nodes + all_generated_summaries

    def _summarize_summaries(
        self, child_summaries: list[TextNode], level: int, summarizer: LLMSummarizer, index: int
    ) -> TextNode | None:
        if not child_summaries:
            return None

        combined_text: str = "\n\n".join(
            node.text for node in child_summaries if node.text and node.text.strip()
        ).strip()

        if not combined_text:
            return None

        summary_text: str = combined_text
        if len(combined_text) >= self.min_summarization_length or level == 0:
            summary_text = summarizer.summarize(combined_text)
            if not summary_text.strip() and combined_text:
                summary_text = combined_text

        if not summary_text.strip():
            return None

        reference_node: TextNode = child_summaries[0]
        summary_node: TextNode = self._create_summary_node(reference_node, summary_text, level, index=index)

        for child in child_summaries:
            self._set_parent_child(child, summary_node)

        return summary_node

    def _summarize_level(
        self,
        level_nodes: list[TextNode],
        direct_child_summaries: list[TextNode],
        level: int,
        summarizer: LLMSummarizer,
    ) -> list[TextNode]:
        if not level_nodes:
            return self._handle_empty_level_nodes(direct_child_summaries, level, summarizer)

        summarized_nodes_for_this_level: list[TextNode] = []
        processed_original_node_ids: set[str] = set()
        current_index_for_level: int = 0

        for node in level_nodes:
            if node.node_id in processed_original_node_ids:
                continue

            summary_node = self._process_node_group(
                node, processed_original_node_ids, direct_child_summaries, 
                level, summarizer, current_index_for_level
            )
            
            if summary_node:
                summarized_nodes_for_this_level.append(summary_node)
                current_index_for_level += 1

        return summarized_nodes_for_this_level

    def _handle_empty_level_nodes(
        self, direct_child_summaries: list[TextNode], level: int, summarizer: LLMSummarizer
    ) -> list[TextNode]:
        """Handle the case when level_nodes is empty."""
        if not direct_child_summaries:
            return []
            
        summary_node = self._summarize_summaries(direct_child_summaries, level, summarizer, index=0)
        return [summary_node] if summary_node else []

    def _process_node_group(
        self,
        node: TextNode,
        processed_original_node_ids: set[str],
        direct_child_summaries: list[TextNode],
        level: int,
        summarizer: LLMSummarizer,
        current_index: int,
    ) -> TextNode | None:
        """Process a group of nodes that should be summarized together."""
        # Collect all nodes in the current group
        current_group_original_nodes = self._collect_grouped_nodes(node, processed_original_node_ids, level)
        
        # Get relevant child summaries
        relevant_hierarchical_children = self._get_relevant_child_summaries(node, direct_child_summaries)
        
        # Create summary text
        summary_text = self._create_summary_text(
            current_group_original_nodes, relevant_hierarchical_children, level, summarizer
        )
        
        if not summary_text.strip():
            return None

        # Create and configure summary node
        summary_node = self._create_summary_node(node, summary_text, level, index=current_index)
        self._establish_parent_child_relationships(
            summary_node, current_group_original_nodes, relevant_hierarchical_children
        )
        
        return summary_node

    def _collect_grouped_nodes(
        self, start_node: TextNode, processed_original_node_ids: set[str], level: int
    ) -> list[TextNode]:
        """Collect all nodes that should be grouped together for summarization."""
        current_group_original_nodes: list[TextNode] = [start_node]
        processed_original_node_ids.add(start_node.node_id)
        temp_curr: TextNode = start_node

        while NodeRelationship.NEXT in temp_curr.relationships:
            next_node = self._get_next_groupable_node(temp_curr, start_node, level, processed_original_node_ids)
            if not next_node:
                break
                
            current_group_original_nodes.append(next_node)
            processed_original_node_ids.add(next_node.node_id)
            temp_curr = next_node

        return current_group_original_nodes

    def _get_next_groupable_node(
        self, current_node: TextNode, start_node: TextNode, level: int, processed_ids: set[str]
    ) -> TextNode | None:
        """Get the next node that can be grouped with the current node."""
        next_node_id = current_node.relationships[NodeRelationship.NEXT].node_id
        next_node_obj = self.node_id_to_node.get(next_node_id)

        if not self._is_node_groupable(next_node_obj, start_node, level, processed_ids):
            return None
            
        return next_node_obj

    def _is_node_groupable(
        self, node: TextNode | None, reference_node: TextNode, level: int, processed_ids: set[str]
    ) -> bool:
        """Check if a node can be grouped with the reference node."""
        return (
            node is not None
            and isinstance(node, TextNode)
            and node.node_id not in processed_ids
            and self._get_summary_level(node) == level
            and self._headers_match_for_grouping(reference_node, node, level)
        )

    def _create_summary_text(
        self,
        original_nodes: list[TextNode],
        child_summaries: list[TextNode],
        level: int,
        summarizer: LLMSummarizer,
    ) -> str:
        """Create summary text from original nodes and child summaries."""
        combined_text_sources = original_nodes + child_summaries
        combined_text = "\n\n".join(
            n.text for n in combined_text_sources if n.text and n.text.strip()
        ).strip()

        if not combined_text:
            return ""

        # Apply summarization if needed
        if len(combined_text) >= self.min_summarization_length or level == 0:
            summary_text = summarizer.summarize(combined_text)
            return summary_text if summary_text.strip() else combined_text
        
        return combined_text

    def _establish_parent_child_relationships(
        self, summary_node: TextNode, original_nodes: list[TextNode], child_summaries: list[TextNode]
    ) -> None:
        """Establish parent-child relationships between summary node and its sources."""
        for source_node in original_nodes:
            self._set_parent_child(source_node, summary_node)
        for child_sum_source in child_summaries:
            self._set_parent_child(child_sum_source, summary_node)

    @staticmethod
    def _is_node_truly_headerless(node: TextNode) -> bool:
        return not any(node.metadata.get(f"h{i}") for i in range(1, 7))

    def _headers_match_for_grouping(self, node1: TextNode, node2: TextNode, level: int) -> bool:
        if level == 0:
            return self._is_node_truly_headerless(node1) and self._is_node_truly_headerless(node2)

        for i in range(1, level + 1):
            h_key: str = f"h{i}"
            if node1.metadata.get(h_key) != node2.metadata.get(h_key):
                return False
        return True

    @staticmethod
    def _create_summary_node(
        original_node: TextNode, summary_text: str, level: int = 0, index: int | None = None
    ) -> TextNode:
        metadata: dict[str, Any] = {
            **original_node.metadata,
            TYPE: NODE_TYPE_SUMMARY,
            HEADING_LEVEL: level,
        }
        if index is not None:
            metadata[INDEX] = index

        summary_node = TextNode(
            text=summary_text,
            metadata=metadata,
            relationships={},
        )

        if NodeRelationship.SOURCE in original_node.relationships:
            summary_node.relationships[NodeRelationship.SOURCE] = original_node.relationships[NodeRelationship.SOURCE]
        return summary_node

    @staticmethod
    def _set_parent_child(child_node: TextNode, parent_node: TextNode) -> None:
        child_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id=parent_node.node_id)
        child_info: RelatedNodeInfo = RelatedNodeInfo(node_id=child_node.node_id)

        if NodeRelationship.CHILD not in parent_node.relationships:
            parent_node.relationships[NodeRelationship.CHILD] = []

        child_list = parent_node.relationships[NodeRelationship.CHILD]
        if isinstance(child_list, list):
            existing_child_ids: set[str] = {r.node_id for r in child_list}
            if child_node.node_id not in existing_child_ids:
                child_list.append(child_info)

    @staticmethod
    def _get_summary_level(node: TextNode) -> int:
        node_type = node.metadata.get(TYPE)
        if node_type == NODE_TYPE_SUMMARY:
            level = node.metadata.get(HEADING_LEVEL)
            if isinstance(level, int):
                return level

        for i in range(1, 7):
            if node.metadata.get(f"h{i}") is not None:
                is_deepest_at_this_h_level: bool = True
                for j in range(i + 1, 7):
                    if node.metadata.get(f"h{j}") is not None:
                        is_deepest_at_this_h_level = False
                        break
                if is_deepest_at_this_h_level:
                    return i
        return 0

    def _group_nodes_by_level(self, nodes: list[TextNode]) -> dict[int, list[TextNode]]:
        grouped_nodes = {}
        for node in nodes:
            level = self._get_summary_level(node)
            grouped_nodes.setdefault(level, []).append(node)
        return grouped_nodes

    def _get_relevant_child_summaries(self, parent_node: TextNode, child_summaries: list[TextNode]) -> list[TextNode]:
        return [child for child in child_summaries if self._is_child_of(child, parent_node)]

    def _is_child_of(self, child_node: TextNode, parent_node: TextNode) -> bool:
        child_headers = self._get_header_hierarchy(child_node)
        parent_headers = self._get_header_hierarchy(parent_node)
        return len(child_headers) == len(parent_headers) + 1 and child_headers[:-1] == parent_headers

    @staticmethod
    def _get_header_hierarchy(node: TextNode) -> list[str]:
        headers = []
        for i in range(1, 7):
            header = node.metadata.get(f"h{i}")
            if header is not None:
                headers.append(header)
            else:
                break
        return headers
