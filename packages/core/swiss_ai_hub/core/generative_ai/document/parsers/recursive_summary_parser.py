import logging
from collections.abc import Callable
from typing import Any

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from openai import BadRequestError

from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    HEADING_LEVEL,
    INDEX,
    LANGUAGE,
    NODE_CONTENT_TYPE,
    NODE_CONTENT_TYPE_TEXT,
    NODE_LANGUAGE_ENGLISH,
    NODE_TYPE_SUMMARY,
    SECTION_START_LINE,
    TYPE,
)

logger = logging.getLogger(__name__)

DEFAULT_SUMMARIZATION_MAX_INPUT_TOKENS = 32768  # conservative default; Infomaniak serves gemma-4-31B-it at 100000

# Absorbs the prompt-template overhead the budget check cannot measure until render time and the tokenizer
# mismatch between our counter and the model actually enforcing the limit.
SUMMARIZATION_BUDGET_SAFETY_FACTOR = 0.85

# Worst-case tokens per character assumed by `_fits`'s accept short-circuit. Deployments process Latin-script
# EU-language content (German, English, and other EU languages) -- even a multi-byte accented character
# under byte-level BPE fallback costs at most ~2 tokens, well short of CJK's worst case of ~3. Raise this back
# toward 3 if this pipeline ever needs to process CJK content.
SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER = 2

MAX_REDUCE_ROUNDS = 4


class SummaryDidNotConvergeError(Exception):
    """A section still exceeds the token budget after MAX_REDUCE_ROUNDS of map-reduce."""


class LLMSummarizer:
    def __init__(
        self,
        llm: LLM,
        t: LocaleHandler,
        max_input_tokens: int = DEFAULT_SUMMARIZATION_MAX_INPUT_TOKENS,
        token_counter: Callable[[str], list[int]] | None = None,
    ):
        self._llm: LLM = llm
        prompt_str: str = t("lib.prompt.summarizer.summarize")
        self._summarize_prompt_template: PromptTemplate = PromptTemplate(prompt_str)
        self._token_counter = token_counter
        self._budget = int(max_input_tokens * SUMMARIZATION_BUDGET_SAFETY_FACTOR)

        # The splitter only ever sees raw text, but `_fits` measures the rendered template around it. Sizing
        # the splitter to the full budget let it hand back chunks that were already over budget once wrapped,
        # for any budget where the fixed template overhead isn't dwarfed by the safety factor's margin.
        template_overhead = self._count_tokens(self._summarize_prompt_template.format(text=""))
        self._splitter = SentenceSplitter(
            chunk_size=max(1, self._budget - template_overhead),
            chunk_overlap=0,
            tokenizer=lambda text: [0] * self._count_tokens(text),
        )

    def summarize(self, text: str) -> str:
        if not text or not text.strip():
            return ""
        return self._summarize_within_budget(text, reduce_round=0)

    def _summarize_within_budget(self, text: str, reduce_round: int) -> str:
        if self._fits(text):
            return self._predict(text)
        if reduce_round >= MAX_REDUCE_ROUNDS:
            raise SummaryDidNotConvergeError(
                f"summary did not converge within {MAX_REDUCE_ROUNDS} reduce rounds "
                f"({self._count_tokens(text)} tokens against a {self._budget}-token budget)"
            )
        partial = [
            self._predict(batch) if already_fits else self._summarize_within_budget(batch, reduce_round + 1)
            for batch, already_fits in self._batches(text)
        ]
        return self._summarize_within_budget("\n\n".join(p for p in partial if p), reduce_round + 1)

    def _batches(self, text: str) -> list[tuple[str, bool]]:
        """
        Group paragraphs into batches that fit, measuring the joined string that will actually be sent.

        Additive per-segment token counts drift from the real payload once separators and boundary effects
        accumulate over many segments. Halving the segment list instead measures the real payload and always
        makes progress, so it cannot loop.

        Each batch is tagged with whether `_fits` already confirmed it, so the caller can predict directly
        instead of re-measuring a string that hasn't changed since. Splitter leaves are tagged False:
        `SentenceSplitter`'s boundary math is close but unverified, so they still need the recursive re-check
        (and its termination bound) as a safety net.
        """

        def group(segments: list[str]) -> list[tuple[str, bool]]:
            joined = "\n\n".join(segments)
            if self._fits(joined):
                return [(joined, True)]
            if len(segments) == 1:
                return [(leaf, False) for leaf in self._splitter.split_text(segments[0])]
            mid = len(segments) // 2
            return group(segments[:mid]) + group(segments[mid:])

        return group(text.split("\n\n"))

    def _fits(self, text: str) -> bool:
        """
        Decide whether `text`, once wrapped in the summarize prompt, is within budget.

        For the Latin-script EU-language content this pipeline processes, a character never costs more than
        `SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER` tokens, so a render at or under `budget /
        SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER` is guaranteed to fit without the network round trip
        `_count_tokens` costs. Symmetrically, no tokenizer we route through produces more than one token per
        character, so a render past 4x the budget is guaranteed to overflow it. That round trip is only
        load-bearing in the boundary between those two — never on a whole oversized document or a large
        map-reduce batch, which the reject short-circuit keeps off `/utils/token_counter` entirely.
        """
        rendered = self._summarize_prompt_template.format(text=text)
        if len(rendered) <= self._budget // SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER:
            return True
        if len(rendered) > self._budget * 4:
            return False
        return self._count_tokens(rendered) <= self._budget

    def _count_tokens(self, text: str) -> int:
        if self._token_counter is None:
            return len(text) // 4
        return len(self._token_counter(text))

    def _predict(self, text: str) -> str:
        response: str = self._llm.predict(self._summarize_prompt_template, text=text)
        return response.strip()


class RecursiveNodeSummarizer:
    def __init__(
        self,
        llm: LLM,
        min_summarization_length: int = 250,
        max_input_tokens: int = DEFAULT_SUMMARIZATION_MAX_INPUT_TOKENS,
        token_counter: Callable[[str], list[int]] | None = None,
    ):
        self._llm = llm
        self.min_summarization_length = min_summarization_length
        self._max_input_tokens = max_input_tokens
        self._token_counter = token_counter
        self.node_id_to_node = {}

    @trace_fn
    def summarize_nodes(self, nodes: list[TextNode]) -> list[TextNode]:
        if not nodes:
            return []

        locale = nodes[0].metadata.get(LANGUAGE, NODE_LANGUAGE_ENGLISH)
        locale_handler = LocaleHandler(locale=locale)
        llm_summarizer: LLMSummarizer = LLMSummarizer(
            llm=self._llm,
            t=locale_handler,
            max_input_tokens=self._max_input_tokens,
            token_counter=self._token_counter,
        )

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

        reference_node: TextNode = child_summaries[0]
        summary_text: str | None = self._summarize_combined_text(combined_text, level, summarizer, reference_node)
        if summary_text is None:
            return None

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
        summarized_nodes_for_this_level: list[TextNode] = []
        processed_original_node_ids: set[str] = set()
        current_index_for_level: int = 0

        if not level_nodes:
            if direct_child_summaries:
                summary_node_from_children: TextNode | None = self._summarize_summaries(
                    direct_child_summaries, level, summarizer, index=current_index_for_level
                )
                if summary_node_from_children:
                    summarized_nodes_for_this_level.append(summary_node_from_children)
            return summarized_nodes_for_this_level

        for node_idx, node in enumerate(level_nodes):
            if node.node_id in processed_original_node_ids:
                continue

            current_group_original_nodes: list[TextNode] = [node]
            processed_original_node_ids.add(node.node_id)
            temp_curr: TextNode = node

            while NodeRelationship.NEXT in temp_curr.relationships:
                next_node_id: str = temp_curr.relationships[NodeRelationship.NEXT].node_id
                next_node_obj: TextNode | None = self.node_id_to_node.get(next_node_id)

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

            relevant_hierarchical_children: list[TextNode] = self._get_relevant_child_summaries(
                node, direct_child_summaries
            )

            combined_text_sources: list[TextNode] = current_group_original_nodes + relevant_hierarchical_children
            combined_text: str = "\n\n".join(n.text for n in combined_text_sources if n.text and n.text.strip()).strip()

            if not combined_text:
                continue

            summary_text: str | None = self._summarize_combined_text(combined_text, level, summarizer, node)
            if summary_text is None:
                continue

            summary_node: TextNode = self._create_summary_node(node, summary_text, level, index=current_index_for_level)
            current_index_for_level += 1

            for source_node in current_group_original_nodes:
                self._set_parent_child(source_node, summary_node)
            for child_sum_source in relevant_hierarchical_children:
                self._set_parent_child(child_sum_source, summary_node)

            summarized_nodes_for_this_level.append(summary_node)

        return summarized_nodes_for_this_level

    def _summarize_combined_text(
        self, combined_text: str, level: int, summarizer: LLMSummarizer, reference_node: TextNode
    ) -> str | None:
        """
        Return the summary for `combined_text`, or None if it should be skipped.

        Catches summarization failure instead of letting it propagate (deviates from the repo's fail-fast
        convention): one section that cannot be reduced within budget would otherwise abort the whole
        document and discard every sibling summary already completed in this run, sometimes tens of
        minutes of LLM work.
        """
        summary_text = combined_text
        if len(combined_text) >= self.min_summarization_length or level == 0:
            try:
                summary_text = summarizer.summarize(combined_text)
            except (SummaryDidNotConvergeError, BadRequestError) as summarization_failure:
                logger.warning(
                    "Skipping summary for %s: %s",
                    self._get_header_hierarchy(reference_node),
                    summarization_failure,
                )
                return None
            if not summary_text.strip() and combined_text:
                summary_text = combined_text

        return summary_text if summary_text.strip() else None

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

        metadata[NODE_CONTENT_TYPE] = NODE_CONTENT_TYPE_TEXT
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
