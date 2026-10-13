import pytest

from swiss_ai_hub.core.displayers.parser.tool_call_markup import ToolCallMarkup
from swiss_ai_hub.core.displayers.parser.tool_call_stream_scrubber import ToolCallStreamScrubber

# Kimi's native tool-call tokens, reaching content because the serving layer never parsed them.
KIMI = (
    "<|tool_calls_section_begin|><|tool_call_begin|>functions.generate_image:3"
    '<|tool_call_argument_begin|>{"prompt": "A vast, deep blue ocean"}'
    "<|tool_call_end|><|tool_calls_section_end|>"
)

HERMES = '<tool_call>{"name": "generate_image", "arguments": {"prompt": "An ocean"}}</tool_call>'

# A captured gemma-4-31B-it response: a tool call imitated from training data, with no tool offered.
REACT = (
    "{\n"
    '  "action": "dalle.text2im",\n'
    '  "action_input": "{ \\"prompt\\": \\"A cozy, modern living room.\\" }",\n'
    '  "thought": "The user wants an image of a sofa in a living room."\n'
    "}"
)


class TestOpensReactObject:
    @pytest.mark.parametrize(
        "text",
        [
            REACT,
            '{"action":"x"}',
            '  {\n\t"action"  :  "x" }',
        ],
    )
    def test_recognizes_react_objects(self, text: str) -> None:
        assert ToolCallMarkup.opens_react_object(text)

    @pytest.mark.parametrize(
        "text",
        [
            'The `action_input` field is a JSON string. Set "action" to the tool name.',
            '{"actionType": "create"}',
            'Here is an example:\n{"action": "run"}',
            '{"name": "generate_image"}',
            "",
        ],
    )
    def test_leaves_everything_else_alone(self, text: str) -> None:
        assert not ToolCallMarkup.opens_react_object(text)


class TestMayOpenReactObject:
    @pytest.mark.parametrize("text", ["", "{", '{\n  "act', '{"action"'])
    def test_viable_prefixes_are_withheld(self, text: str) -> None:
        assert ToolCallMarkup.may_open_react_object(text)

    @pytest.mark.parametrize("text", ["Hello", '{"name"', "The image", "{}"])
    def test_ruled_out_prefixes_flow_immediately(self, text: str) -> None:
        assert not ToolCallMarkup.may_open_react_object(text)


class TestStrip:
    def test_removes_kimi_span(self) -> None:
        assert ToolCallMarkup.strip(f"Here you go.{KIMI}") == "Here you go."

    def test_removes_hermes_span(self) -> None:
        assert ToolCallMarkup.strip(f"Here you go.{HERMES}") == "Here you go."

    def test_blanks_a_whole_message_react_object(self) -> None:
        assert ToolCallMarkup.strip(REACT) == ""

    def test_unterminated_span_runs_to_the_end(self) -> None:
        assert ToolCallMarkup.strip("Wait.<|tool_calls_section_begin|>truncated...") == "Wait."

    def test_prose_survives_untouched(self) -> None:
        prose = 'The `action_input` field is a JSON string. Set "action" to the tool name.'
        assert ToolCallMarkup.strip(prose) == prose


class TestToolCallStreamScrubber:
    @staticmethod
    def _run(text: str, size: int = 7) -> str:
        """Feed in small chunks so every delimiter straddles a chunk boundary."""
        scrubber = ToolCallStreamScrubber()
        forwarded = "".join(scrubber.feed(text[i : i + size]) for i in range(0, len(text), size))
        return forwarded + scrubber.flush()

    @pytest.mark.parametrize("markup", [KIMI, HERMES, REACT])
    def test_markup_never_reaches_the_client(self, markup: str) -> None:
        assert self._run(markup) == ""

    def test_prose_around_a_span_is_preserved(self) -> None:
        assert self._run(f"Before. {KIMI} After.") == "Before.  After."

    @pytest.mark.parametrize(
        "prose",
        [
            "The image you requested has been generated and is shown above.",
            'The `action_input` field is a JSON string. Set "action" to the tool name.',
            "<think>Reasoning stays, the client renders it.</think>Here is your answer.",
            '{"name": "generate_image", "size": "1024x1024"} is the payload.',
        ],
    )
    def test_ordinary_content_passes_through_unchanged(self, prose: str) -> None:
        assert self._run(prose) == prose

    def test_single_character_chunks(self) -> None:
        assert self._run(f"Hi.{HERMES}", size=1) == "Hi."
