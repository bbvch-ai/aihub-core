import pytest

from swiss_ai_hub.core.displayers.stream.stream_processor import StreamProcessor

# Kimi's native tool-call tokens, reaching content because the serving layer never parsed them.
KIMI = (
    "<|tool_calls_section_begin|><|tool_call_begin|>functions.generate_image:3"
    '<|tool_call_argument_begin|>{"prompt": "A vast, deep blue ocean"}'
    "<|tool_call_end|><|tool_calls_section_end|>"
)

# A captured LLMWrappingAgent stream on gemma-4-31B-it, chunked as it actually arrived: every chunk
# of the answer is markup, so nothing is left once it is suppressed.
SOFA_RUN = [
    "{\n",
    '  "action": "dalle.',
    'text2im",\n',
    '  "action_input": "{ \\"prompt\\": \\"A cozy, modern living room featuring a sofa as the centerpiece.',
    " The room should have warm lighting, a soft rug, a coffee table, and some indoor plants.",
    " High resolution, photorealistic style.",
    '\\" }",\n',
    '  "thought": "The user wants an image of a sofa in a living room.',
    " I will generate a photorealistic image of a cozy modern living room.",
    '"\n',
    "}",
]


class StubDisplayer:
    def __init__(self):
        self.chunks: list[str] = []
        self.thoughts: list[str] = []

    async def display_chunk(self, content: str, model_name: str) -> None:
        self.chunks.append(content)

    async def display_thought(self, thought: str) -> None:
        self.thoughts.append(thought)


async def _stream(chunks: list[str]) -> tuple[StubDisplayer, str]:
    displayer = StubDisplayer()
    processor = StreamProcessor(displayer, "text-generation/gemma-4-31B-it")
    for chunk in chunks:
        await processor.process_chunk(chunk)
    return displayer, await processor.finalize()


def _split(text: str, size: int = 7) -> list[str]:
    """Split small enough that the decision straddles chunk boundaries, as a real stream does."""
    return [text[i : i + size] for i in range(0, len(text), size)]


@pytest.mark.asyncio
async def test_react_object_never_reaches_the_answer() -> None:
    displayer, aggregate = await _stream(SOFA_RUN)

    assert displayer.chunks == []
    assert aggregate == ""
    assert '"action": "dalle.text2im"' in "".join(displayer.thoughts)


@pytest.mark.asyncio
async def test_kimi_span_never_reaches_the_answer() -> None:
    displayer, aggregate = await _stream(_split(KIMI))

    assert "".join(displayer.chunks) == ""
    assert "<|tool_call" not in aggregate


@pytest.mark.asyncio
async def test_prose_around_a_span_still_answers() -> None:
    displayer, aggregate = await _stream(_split(f"Here is your image.{KIMI}"))

    assert "".join(displayer.chunks) == "Here is your image."
    assert aggregate == "Here is your image."


@pytest.mark.asyncio
async def test_bare_closing_think_tag_is_still_consumed() -> None:
    """Some chat templates pre-fill ``<think>``, so the model emits only the closing tag."""
    displayer, _ = await _stream(_split("Reasoning here.</think>The real answer."))

    assert "".join(displayer.chunks) == "Reasoning here.The real answer."


@pytest.mark.asyncio
async def test_reasoning_tags_are_unaffected() -> None:
    displayer, _ = await _stream(_split("<think>I should describe an ocean.</think>Vast and blue."))

    assert "".join(displayer.chunks) == "Vast and blue."
    assert "".join(displayer.thoughts) == "I should describe an ocean."


@pytest.mark.asyncio
async def test_prose_mentioning_tool_call_keys_survives() -> None:
    prose = 'The `action_input` field is a JSON string. Set "action" to the tool name.'
    displayer, aggregate = await _stream(_split(prose))

    assert "".join(displayer.chunks) == prose
    assert aggregate == prose


@pytest.mark.asyncio
async def test_answer_that_merely_starts_with_a_brace_still_streams() -> None:
    """The gate withholds only while ``{"action":`` is still possible, never longer."""
    snippet = '{"name": "generate_image", "size": "1024x1024"} is the payload.'
    displayer, aggregate = await _stream(_split(snippet))

    assert "".join(displayer.chunks) == snippet
    assert aggregate == snippet


@pytest.mark.asyncio
async def test_a_well_behaved_caption_is_untouched() -> None:
    caption = "The image you requested has been generated and is shown above."
    displayer, aggregate = await _stream(["The image ", "you requested has been ", "generated and is shown above."])

    assert "".join(displayer.chunks) == caption
    assert aggregate == caption
