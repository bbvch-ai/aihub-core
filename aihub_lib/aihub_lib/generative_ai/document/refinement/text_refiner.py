"""LLM-based text refinement for document cleanup.

Fixes OCR errors, broken paragraphs, and encoding issues from PDF extraction.
"""

import logging
import re
from collections.abc import Callable
from typing import TYPE_CHECKING

from llama_index.core import PromptTemplate

if TYPE_CHECKING:
    from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

_logger = logging.getLogger(__name__)

_DEFAULT_MAX_CHUNK_TOKENS = 4000  # Leave room for prompt and response
_TABLE_PATTERN = re.compile(r"<table>.*?</table>", re.DOTALL)
_FIGURE_PATTERN = re.compile(r"<figure>.*?</figure>", re.DOTALL)


def refine_document_text(
    markdown_text: str, llm_config: "LLMConfig", max_chunk_tokens: int = _DEFAULT_MAX_CHUNK_TOKENS
) -> str:
    """Refine document text using LLM. Preserves <table> and <figure> tags."""
    _logger.debug("Starting LLM text refinement")

    text, placeholders = _extract_special_elements(markdown_text)
    _logger.debug(f"Extracted {len(placeholders)} special elements (tables/figures)")

    token_counter = _create_token_counter(llm_config)
    chunks = _split_into_chunks(text, token_counter, max_chunk_tokens)
    _logger.debug(f"Split text into {len(chunks)} chunks for processing (max {max_chunk_tokens} tokens each)")

    refined_chunks = []
    for i, chunk in enumerate(chunks):
        try:
            _logger.debug(f"Refining chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)")
            refined = _refine_chunk(chunk, llm_config)
            refined_chunks.append(refined)
        except Exception as e:
            _logger.warning(f"Failed to refine chunk {i + 1}/{len(chunks)}, keeping original: {e}")
            refined_chunks.append(chunk)

    refined_text = "".join(refined_chunks)
    refined_text = _restore_special_elements(refined_text, placeholders)

    _logger.debug("LLM text refinement complete")
    return refined_text


def _extract_special_elements(text: str) -> tuple[str, dict[str, str]]:
    """Extract tables and figures, replacing with placeholders."""
    placeholders: dict[str, str] = {}
    counter = 0

    def replace_with_placeholder(match: re.Match, element_type: str) -> str:
        nonlocal counter
        placeholder = f"__PLACEHOLDER_{element_type}_{counter}__"
        placeholders[placeholder] = match.group(0)
        counter += 1
        return placeholder

    text = _TABLE_PATTERN.sub(lambda m: replace_with_placeholder(m, "TABLE"), text)
    text = _FIGURE_PATTERN.sub(lambda m: replace_with_placeholder(m, "FIGURE"), text)

    return text, placeholders


def _restore_special_elements(text: str, placeholders: dict[str, str]) -> str:
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    return text


def _create_token_counter(llm_config: "LLMConfig") -> Callable[[str], int]:
    """Create a token counter function from LLMConfig."""
    raw_counter = llm_config.token_counter

    def count_tokens(text: str) -> int:
        return len(raw_counter(text))

    return count_tokens


def _split_into_chunks(text: str, token_counter: Callable[[str], int], max_tokens: int) -> list[str]:
    """Split text into chunks based on token count, respecting paragraph boundaries."""
    total_tokens = token_counter(text)
    if total_tokens <= max_tokens:
        return [text]

    chunks = []
    current_chunk = ""
    current_tokens = 0
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        para_tokens = token_counter(para)
        separator_tokens = token_counter("\n\n") if current_chunk else 0

        if current_tokens + para_tokens + separator_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para
            current_tokens = para_tokens
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
            current_tokens += para_tokens + separator_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _refine_chunk(chunk: str, llm_config: "LLMConfig") -> str:
    prompt_text = """You are a document text refinement assistant. Clean up the following text \
extracted from a PDF document.

Fix these issues while preserving the original meaning and markdown formatting:

1. **OCR Errors**: Fix garbled characters, misrecognized letters (e.g., "rn" misread as "m", "l" as "1", "O" as "0")
2. **Broken Words**: Rejoin words split across lines with hyphens (e.g., "docu-\\nment" → "document")
3. **Structural Artifacts**: Remove stray characters, fix broken paragraphs, normalize spacing
4. **Encoding Issues**: Fix special characters that weren't decoded properly
5. **Preserve Placeholders**: Keep any __PLACEHOLDER_*__ strings exactly as they are

Important:
- Keep all markdown formatting (headers, lists, bold, italic, links)
- Do NOT add, remove, or change the actual content/meaning
- Do NOT translate or paraphrase
- Do NOT add explanations or commentary
- Return ONLY the refined text

Text to refine:
{text}

Refined text:"""

    prompt = PromptTemplate(prompt_text)

    llm, _ = llm_config.to_llama_index()
    response = llm.predict(prompt, text=chunk)

    # Clean up any potential artifacts from LLM response
    refined = response.strip()

    # Remove any "Refined text:" prefix the LLM might have added
    if refined.lower().startswith("refined text:"):
        refined = refined[13:].strip()

    return refined
