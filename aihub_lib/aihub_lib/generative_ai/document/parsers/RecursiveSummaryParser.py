from typing import Any, Dict, List, Optional, Tuple

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
        self._llm: LLM = llm
        self.min_summarization_length: int = min_summarization_length
        self.node_id_to_node: Dict[str, TextNode] = {}

    def summarize_nodes(self, nodes: List[TextNode]) -> List[TextNode]:
        if not nodes:
            return []

        locale_str: str = NODE_LANGUAGE_ENGLISH
        for node_meta_check in nodes:
            if LANGUAGE in node_meta_check.metadata:
                meta_lang = node_meta_check.metadata[LANGUAGE]
                if isinstance(meta_lang, str):  # Ensure it's a string
                    locale_str = meta_lang
                    break

        locale_handler: LocaleHandler = LocaleHandler(locale=locale_str)
        llm_summarizer: LLMSummarizer = LLMSummarizer(llm=self._llm, t=locale_handler)

        self.node_id_to_node = {node.node_id: node for node in nodes}

        grouped_nodes: Dict[int, List[TextNode]] = self._group_nodes_by_level(nodes)
        for level_nodes_list in grouped_nodes.values():
            level_nodes_list.sort(key=lambda n: n.metadata.get("section_start_line", float("inf")))

        max_level: int = max(grouped_nodes.keys()) if grouped_nodes else -1

        all_generated_summaries: List[TextNode] = []

        for level in range(max_level, -1, -1):
            original_nodes_at_this_level: List[TextNode] = grouped_nodes.get(level, [])

            child_summaries_for_this_level: List[TextNode] = [
                s_node for s_node in all_generated_summaries if s_node.metadata.get(HEADING_LEVEL) == level + 1
            ]

            summarized_nodes_at_this_level: List[TextNode] = self._summarize_level(
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
        self, child_summaries: List[TextNode], level: int, summarizer: LLMSummarizer, index: int
    ) -> Optional[TextNode]:
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
        level_nodes: List[TextNode],
        direct_child_summaries: List[TextNode],
        level: int,
        summarizer: LLMSummarizer,
    ) -> List[TextNode]:
        summarized_nodes_for_this_level: List[TextNode] = []
        processed_original_node_ids: set[str] = set()
        current_index_for_level: int = 0

        if not level_nodes:
            if direct_child_summaries:
                summary_node_from_children: Optional[TextNode] = self._summarize_summaries(
                    direct_child_summaries, level, summarizer, index=current_index_for_level
                )
                if summary_node_from_children:
                    summarized_nodes_for_this_level.append(summary_node_from_children)
            return summarized_nodes_for_this_level

        for node_idx, node in enumerate(level_nodes):
            if node.node_id in processed_original_node_ids:
                continue

            current_group_original_nodes: List[TextNode] = [node]
            processed_original_node_ids.add(node.node_id)
            temp_curr: TextNode = node

            while NodeRelationship.NEXT in temp_curr.relationships:
                next_node_id: str = temp_curr.relationships[NodeRelationship.NEXT].node_id
                next_node_obj: Optional[TextNode] = self.node_id_to_node.get(next_node_id)

                if (
                    next_node_obj
                    and isinstance(next_node_obj, TextNode)
                    and self._get_summary_level(next_node_obj) == level
                    and self._headers_match_for_grouping(node, next_node_obj, level)
                ):
                    if next_node_obj.node_id in processed_original_node_ids:
                        break
                    current_group_original_nodes.append(next_node_obj)
                    processed_original_node_ids.add(next_node_obj.node_id)
                    temp_curr = next_node_obj
                else:
                    break

            relevant_hierarchical_children: List[TextNode] = self._get_relevant_child_summaries(
                node, direct_child_summaries
            )

            combined_text_sources: List[TextNode] = current_group_original_nodes + relevant_hierarchical_children
            combined_text: str = "\n\n".join(n.text for n in combined_text_sources if n.text and n.text.strip()).strip()

            if not combined_text:
                continue

            summary_text: str = combined_text
            if len(combined_text) >= self.min_summarization_length or level == 0:
                summary_text = summarizer.summarize(combined_text)
                if not summary_text.strip() and combined_text:
                    summary_text = combined_text

            if not summary_text.strip():
                continue

            summary_node: TextNode = self._create_summary_node(node, summary_text, level, index=current_index_for_level)
            current_index_for_level += 1

            for source_node in current_group_original_nodes:
                self._set_parent_child(source_node, summary_node)
            for child_sum_source in relevant_hierarchical_children:
                self._set_parent_child(child_sum_source, summary_node)

            summarized_nodes_for_this_level.append(summary_node)

        return summarized_nodes_for_this_level

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
        original_node: TextNode, summary_text: str, level: int = 0, index: Optional[int] = None
    ) -> TextNode:
        metadata: Dict[str, Any] = {
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
            source_rel: RelatedNodeInfo = original_node.relationships[NodeRelationship.SOURCE]
            summary_node.relationships[NodeRelationship.SOURCE] = source_rel
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

    def _group_nodes_by_level(self, nodes: List[TextNode]) -> Dict[int, List[TextNode]]:
        grouped_nodes: Dict[int, List[TextNode]] = {}
        for node in nodes:
            level: int = self._get_summary_level(node)
            grouped_nodes.setdefault(level, []).append(node)
        return grouped_nodes

    def _get_relevant_child_summaries(
        self, parent_ref_node: TextNode, direct_child_summaries: List[TextNode]
    ) -> List[TextNode]:
        relevant_children: List[TextNode] = []
        parent_level: int = self._get_summary_level(parent_ref_node)
        parent_headers_prefix_tuple: Tuple[Optional[Any], ...] = self._get_header_hierarchy_values_tuple(
            parent_ref_node, parent_level
        )

        for child_summary in direct_child_summaries:
            child_summary_heading_level = child_summary.metadata.get(HEADING_LEVEL)
            if isinstance(child_summary_heading_level, int) and child_summary_heading_level == parent_level + 1:
                child_lineage_prefix_tuple: Tuple[Optional[Any], ...] = self._get_header_hierarchy_values_tuple(
                    child_summary, parent_level
                )
                if child_lineage_prefix_tuple == parent_headers_prefix_tuple:
                    relevant_children.append(child_summary)
        return relevant_children

    @staticmethod
    def _get_header_hierarchy_values_tuple(node: TextNode, depth: int) -> Tuple[Optional[str], ...]:
        return tuple(node.metadata.get(f"h{i}") for i in range(1, depth + 1))
