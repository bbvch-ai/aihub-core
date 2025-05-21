from typing import Dict, List

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
    TYPE,
)


class LLMSummarizer:
    def __init__(self, llm: LLM, t: LocaleHandler):
        self._llm = llm
        self._summarize_prompt_template = PromptTemplate(t("lib.prompt.summarizer.summarize"))

    def summarize(self, text: str) -> str:
        response = self._llm.predict(self._summarize_prompt_template, text=text)
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

    def summarize_nodes(self, nodes: List[TextNode]) -> List[TextNode]:
        if not nodes:
            return []
        locale = nodes[0].metadata.get(LANGUAGE, NODE_LANGUAGE_ENGLISH)
        locale_handler = LocaleHandler(locale=locale)
        llm_summarizer = LLMSummarizer(llm=self._llm, t=locale_handler)
        self.node_id_to_node = {node.node_id: node for node in nodes}

        grouped_nodes = self._group_nodes_by_level(nodes)
        max_level = max(grouped_nodes.keys()) if grouped_nodes else 0

        summary_nodes = []
        level_indices = {level: 0 for level in range(max_level + 1)}

        for level in range(max_level, -1, -1):
            level_nodes = grouped_nodes.get(level, [])
            summarized_level_nodes = self._summarize_level(level_nodes, summary_nodes, level, llm_summarizer)

            # First assign indices to all nodes at this level
            for node in sorted(
                summarized_level_nodes, key=lambda n: n.metadata.get(f"h{self._get_summary_level(n)}", "")
            ):
                node.metadata[INDEX] = level_indices[level]
                level_indices[level] += 1

            # Group by parent for relationships
            by_parent = {}
            for node in summarized_level_nodes:
                parent_headers = []
                node_level = self._get_summary_level(node)
                for i in range(1, node_level):
                    header = node.metadata.get(f"h{i}")
                    if header:
                        parent_headers.append((i, header))

                parent_key = tuple(parent_headers)
                if parent_key not in by_parent:
                    by_parent[parent_key] = []
                by_parent[parent_key].append(node)

            # Establish relationships only between siblings
            for siblings in by_parent.values():
                if len(siblings) < 2:
                    continue

                siblings.sort(key=lambda n: n.metadata.get(f"h{self._get_summary_level(n)}", ""))

                for i, node in enumerate(siblings):
                    if i > 0:
                        node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=siblings[i - 1].node_id)

                    if i < len(siblings) - 1:
                        node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=siblings[i + 1].node_id)

            summary_nodes.extend(summarized_level_nodes)

        return nodes.copy() + summary_nodes

    def _summarize_summaries(self, child_summaries: List[TextNode], level: int, summarizer: LLMSummarizer) -> TextNode:
        combined_text = "\n\n".join(node.text for node in child_summaries)
        if len(combined_text) < self.min_summarization_length and level > 0:
            summary = combined_text
        else:
            summary = summarizer.summarize(combined_text)
        summary_node = self._create_summary_node(child_summaries[0], summary, level)

        for child in child_summaries:
            self._set_parent_child(child, summary_node)

        return summary_node

    def _summarize_level(
        self,
        level_nodes: List[TextNode],
        child_summaries: List[TextNode],
        level: int,
        summarizer: LLMSummarizer,
    ) -> List[TextNode]:
        summarized_nodes = []
        processed_nodes = set()

        if not level_nodes:
            by_parent = {}
            for node in child_summaries:
                if self._get_summary_level(node) == level + 1:
                    headers = tuple(self._get_header_hierarchy(node)[:-1])
                    if headers not in by_parent:
                        by_parent[headers] = []
                    by_parent[headers].append(node)

            for summaries in by_parent.values():
                if summaries:
                    level_summary = self._summarize_summaries(summaries, level, summarizer)
                    summarized_nodes.append(level_summary)

            return summarized_nodes

        for node in level_nodes:
            if node.node_id in processed_nodes:
                continue

            next_nodes = self._get_next_nodes(node)
            relevant_child_summaries = self._get_relevant_child_summaries(node, child_summaries)
            combined_text = self._combine_texts(node, next_nodes, relevant_child_summaries)

            if len(combined_text) < self.min_summarization_length and level > 0:
                summary = combined_text
            else:
                summary = summarizer.summarize(combined_text)

            summary_node = self._create_summary_node(node, summary, level)
            self._set_parent_child(node, summary_node)

            for child in relevant_child_summaries:
                self._set_parent_child(child, summary_node)

            for next_node in next_nodes:
                self._set_parent_child(next_node, summary_node)
                processed_nodes.add(next_node.node_id)
            summarized_nodes.append(summary_node)

        return summarized_nodes

    def _get_next_nodes(self, node: TextNode) -> List[TextNode]:
        next_nodes = []
        current_node = node
        visited_nodes = set()
        while NodeRelationship.NEXT in current_node.relationships:
            if current_node.node_id in visited_nodes:
                break
            visited_nodes.add(current_node.node_id)
            next_node_id = current_node.relationships[NodeRelationship.NEXT].node_id
            next_node = self.node_id_to_node.get(next_node_id)
            if not next_node:
                break
            next_nodes.append(next_node)
            current_node = next_node
        return next_nodes

    @staticmethod
    def _create_summary_node(original_node: TextNode, summary: str, level: int = 0) -> TextNode:
        summary_node = TextNode(
            text=summary,
            metadata={
                **original_node.metadata,
                TYPE: NODE_TYPE_SUMMARY,
                HEADING_LEVEL: level,
            },
            relationships={},
        )
        if NodeRelationship.SOURCE in original_node.relationships:
            summary_node.relationships[NodeRelationship.SOURCE] = original_node.relationships[NodeRelationship.SOURCE]
        return summary_node

    @staticmethod
    def _set_parent_child(child_node: TextNode, parent_node: TextNode):
        child_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id=parent_node.node_id)
        if NodeRelationship.CHILD not in parent_node.relationships:
            parent_node.relationships[NodeRelationship.CHILD] = [RelatedNodeInfo(node_id=child_node.node_id)]
        else:
            parent_node.relationships[NodeRelationship.CHILD].append(RelatedNodeInfo(node_id=child_node.node_id))

    @staticmethod
    def _combine_texts(
        current_node: TextNode,
        next_nodes: List[TextNode],
        child_summaries: List[TextNode],
    ) -> str:
        texts = [current_node.text] + [node.text for node in next_nodes] + [child.text for child in child_summaries]
        return "\n\n".join(texts)

    @staticmethod
    def _get_summary_level(node: TextNode) -> int:
        if HEADING_LEVEL in node.metadata:
            return node.metadata[HEADING_LEVEL]

        for level in range(6, 0, -1):
            if node.metadata.get(f"h{level}") is not None:
                return level
        return 0

    def _group_nodes_by_level(self, nodes: List[TextNode]) -> Dict[int, List[TextNode]]:
        grouped_nodes = {}
        for node in nodes:
            level = self._get_summary_level(node)
            grouped_nodes.setdefault(level, []).append(node)
        return grouped_nodes

    def _get_relevant_child_summaries(self, parent_node: TextNode, child_summaries: List[TextNode]) -> List[TextNode]:
        return [child for child in child_summaries if self._is_child_of(child, parent_node)]

    def _is_child_of(self, child_node: TextNode, parent_node: TextNode) -> bool:
        child_headers = self._get_header_hierarchy(child_node)
        parent_headers = self._get_header_hierarchy(parent_node)
        return len(child_headers) == len(parent_headers) + 1 and child_headers[:-1] == parent_headers

    @staticmethod
    def _get_header_hierarchy(node: TextNode) -> List[str]:
        headers = []
        for i in range(1, 7):
            header = node.metadata.get(f"h{i}")
            if header is not None:
                headers.append(header)
            else:
                break
        return headers
