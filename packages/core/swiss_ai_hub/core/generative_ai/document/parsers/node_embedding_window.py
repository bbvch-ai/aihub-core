from llama_index.core.schema import BaseNode, MetadataMode
from pydantic import BaseModel, ConfigDict

from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import INDEX, SOURCE

# A node whose metadata leaves less than this for its content is mostly headings, title and record fields: a parsing
# or source defect to fix, not something to embed with its content cut to a few words.
MIN_CONTENT_TOKENS = 256

# The metadata and the content are counted apart when sizing the room, and tokens merge differently across the
# join than within either side.
JOIN_MARGIN_TOKENS = 8

LARGEST_METADATA_KEYS_NAMED = 3


class NodeEmbeddingWindow(BaseModel):
    """
    Checks a node exactly as the embedding model will receive it: the `MetadataMode.EMBED` text, metadata included,
    plus the model's special tokens.

    The content is capped when it is split, but the metadata prepended to it (h1-h6 heading lines, title, source,
    record fields) has no size bound of its own, so only the whole text tells whether a node fits.
    """

    model_config = ConfigDict(frozen=True)

    budget: ModelTokenBudget

    def tokens(self, node: BaseNode) -> int:
        return self.budget.count_with_overhead(node.get_content(metadata_mode=MetadataMode.EMBED))

    def fits(self, node: BaseNode) -> bool:
        return self.tokens(node) <= self.budget.max_input_tokens

    def content_room(self, node: BaseNode) -> int:
        """Tokens left for the node's content next to its metadata; raises when that is below the floor."""
        metadata_tokens = self.tokens(node.model_copy(update={"text": ""}))
        room = self.budget.max_input_tokens - metadata_tokens - JOIN_MARGIN_TOKENS
        if room < MIN_CONTENT_TOKENS:
            raise ValueError(
                f"The metadata of node {node.metadata.get(INDEX)} of document '{self._document(node)}' takes "
                f"{metadata_tokens} of the {self.budget.max_input_tokens} tokens {self.budget.model_name} accepts, "
                f"leaving {room} for its content (at least {MIN_CONTENT_TOKENS} required). Largest metadata: "
                f"{self._largest_metadata(node)}"
            )
        return room

    def require_fit(self, nodes: list[BaseNode]) -> None:
        for node in nodes:
            tokens = self.tokens(node)
            if tokens > self.budget.max_input_tokens:
                raise ValueError(
                    f"Node {node.node_id} of document '{self._document(node)}' measures {tokens} tokens, over the "
                    f"{self.budget.max_input_tokens} {self.budget.model_name} accepts. Largest metadata: "
                    f"{self._largest_metadata(node)}"
                )

    @staticmethod
    def _document(node: BaseNode) -> str:
        return node.metadata.get(SOURCE) or node.ref_doc_id or "unknown"

    def _largest_metadata(self, node: BaseNode) -> str:
        embedded = {
            key: self.budget.tokenizer.count(str(value))
            for key, value in node.metadata.items()
            if key not in node.excluded_embed_metadata_keys
        }
        largest = sorted(embedded.items(), key=lambda item: item[1], reverse=True)[:LARGEST_METADATA_KEYS_NAMED]
        return ", ".join(f"{key} ({tokens} tokens)" for key, tokens in largest)
