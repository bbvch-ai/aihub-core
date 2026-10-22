"""LiteLLM guardrail: anonymise chat requests through the Presidio analyzer, restore the answer while it streams.

Before the call, every text part of every message (system, user, assistant, tool results) goes to the analyzer and the
detected spans are replaced by numbered placeholders (`<PERSON_1>`), one per distinct value, with overlapping spans
merged first so no placeholder is ever broken. The model only sees placeholders. On the way back the placeholders are
restored in the answer text, the reasoning text and the tool-call arguments, streamed or not; while streaming only a
possible placeholder prefix (a few characters) is held back, so the answer keeps streaming. LiteLLM's built-in Presidio
guardrail cannot do this: it buffers a streamed answer and numbers overlapping spans separately.

It runs on every call to a model whose `model_info.aihub_hosting_location` is not `local` (a model without the field
counts as external), and on a local model when the call requests it by name. Placeholders already in the input (text a
user anonymised by hand) are passed through, never re-detected and never reused for a new value. The placeholder map
is PII, so it lives only in this process, keyed by the request's litellm_call_id, and is never written into request
metadata, which LiteLLM forwards to spend logs and callbacks. A failed or timed-out analysis fails the call.

GLiNER also tags pronouns ("Sie", "vous") as PERSON and field labels ("Adresse", "IBAN") as their own type, and in
long documents numbered labels too ("Position 2"). Masking them garbles the prompt and the answer ("Adresse: Adresse")
and hides line numbers from extraction, so a detection is never masked when it is exactly a word from
`pii_allow_list`, in any case, optionally followed by a short number.

The module is bind-mounted into the upstream LiteLLM image like custom_callbacks.py, so it may only depend on the
stdlib, httpx and LiteLLM. The analyzer URL and key come from PRESIDIO_ANALYZER_API_BASE and PRESIDIO_ANALYZER_API_KEY.
"""

import copy
import json
import logging
import os
import re
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx

try:
    from litellm.integrations.custom_guardrail import CustomGuardrail
    from litellm.types.guardrails import GuardrailEventHooks
except ImportError:
    # litellm is absent outside its own image (e.g. unit tests import this by path).
    CustomGuardrail = object
    GuardrailEventHooks = None

logger = logging.getLogger(__name__)

TOKEN = re.compile(r"<[A-Z][A-Z_]*_\d+>")
PARTIAL_TOKEN = re.compile(r"<[A-Z_]*\d*\Z")
LOCAL_HOSTING = "local"
CHAT_CALL_TYPES = {"completion", "acompletion"}
JSON_RESPONSE_FORMATS = {"json_object", "json_schema"}
# A 20k-token prompt takes about 50 s on the analyzer's 4 CPU threads; past this the call fails instead of hanging.
ANALYZER_TIMEOUT_SECONDS = 150
# A label may carry a short number ("Position 2", "Art. 5", "Nr. 12a"); four digits at most, so no ID or phone fits.
NUMBERED_LABEL_SUFFIX = r"(?:\s*(?:Nr\.?|No\.?|n°)?\s*\d{1,4}[a-z]?)?"
# Maps of calls that never reached a response hook (client gone mid-stream) are dropped after this.
MAP_TTL_SECONDS = 1800


class AnonymisationUnavailableError(Exception):
    """The analyzer could not be reached or failed, so the call is refused rather than sent unmasked."""


class PlaceholderMasker:
    """Replaces detected spans with <TYPE_N>: one placeholder per distinct value, overlapping spans merged first.

    Numbers are shared across types and skip every placeholder already present in the request, so restoring never
    overwrites a placeholder the user brought in. TYPE is upper-cased: the restorer only recognises upper-case
    placeholders, which keeps ordinary markup such as <br> out of its way.
    """

    def __init__(self, reserved: set[str]) -> None:
        self.tokens: dict[str, str] = {}
        self._reserved = reserved
        self._by_value: dict[tuple[str, str], str] = {}
        self._next = 1

    @staticmethod
    def merge_overlaps(spans: list[dict]) -> list[dict]:
        merged: list[dict] = []
        for span in sorted(spans, key=lambda s: (s["start"], -(s["end"] - s["start"]), s["entity_type"])):
            previous = merged[-1] if merged else None
            if previous and span["start"] < previous["end"]:
                if span["end"] - span["start"] > previous["end"] - previous["start"]:
                    previous["entity_type"] = span["entity_type"]
                previous["end"] = max(previous["end"], span["end"])
            else:
                merged.append(dict(span))
        return merged

    def _new_token(self, entity_type: str) -> str:
        while True:
            token = f"<{entity_type.upper()}_{self._next}>"
            self._next += 1
            if token not in self._reserved:
                return token

    def mask(self, text: str, spans: list[dict]) -> str:
        existing = [(m.start(), m.end()) for m in TOKEN.finditer(text)]
        spans = [s for s in spans if not any(s["start"] < end and start < s["end"] for start, end in existing)]
        parts, cursor = [], 0
        for span in self.merge_overlaps(spans):
            value = text[span["start"]:span["end"]]
            key = (span["entity_type"], value)
            if key not in self._by_value:
                token = self._new_token(span["entity_type"])
                self._by_value[key] = token
                self.tokens[token] = value
            parts += [text[cursor:span["start"]], self._by_value[key]]
            cursor = span["end"]
        return "".join(parts + [text[cursor:]])


class StreamRestorer:
    """Restores placeholders in text that arrives in pieces; a placeholder may be split across pieces."""

    def __init__(self, tokens: dict[str, str]) -> None:
        self.tokens = tokens
        self.max_token_length = max(map(len, tokens), default=0)
        self.hold = ""

    def restore(self, text: str) -> str:
        return TOKEN.sub(lambda match: self.tokens.get(match.group(0), match.group(0)), text)

    def feed(self, piece: str) -> str:
        buffer = self.hold + piece
        cut = buffer.rfind("<")
        if cut != -1 and len(buffer) - cut < self.max_token_length and PARTIAL_TOKEN.match(buffer, cut):
            self.hold, buffer = buffer[cut:], buffer[:cut]
        else:
            self.hold = ""
        return self.restore(buffer)

    def flush(self) -> str:
        rest, self.hold = self.restore(self.hold), ""
        return rest


class PiiAnonymisationGuardrail(CustomGuardrail):
    """Masks chat requests through the Presidio analyzer and restores the answer, streamed or not."""

    def __init__(self, presidio_language: str | None = None, pii_entities_config: dict | None = None,
                 pii_allow_list: list[str] | None = None, **kwargs: Any) -> None:
        self.analyze_url = os.environ.get("PRESIDIO_ANALYZER_API_BASE", "http://presidio-analyzer:3000").rstrip("/")
        self.analyze_url += "/analyze"
        self.api_key = os.environ.get("PRESIDIO_ANALYZER_API_KEY", "")
        # The analyzer registers every recognizer under `de` and covers all languages there; the Hub's per-request
        # language hint (guardrail_config.language) would hit languages it has no recognizers for.
        self.language = presidio_language or "de"
        self.entities = [str(getattr(key, "value", key)) for key in (pii_entities_config or {})]
        self.allow_list = self.allow_list_pattern(pii_allow_list or [])
        self.client = httpx.AsyncClient(timeout=ANALYZER_TIMEOUT_SECONDS)
        self._maps: dict[str, tuple[float, dict[str, str], bool]] = {}
        self._external: dict[str, bool] = {}
        super().__init__(**kwargs)

    # ------------------------------------------------------------------ which calls

    def should_run_guardrail(self, data: Any, event_type: Any) -> bool:
        if not isinstance(data, dict) or "messages" not in data:
            return False
        if super().should_run_guardrail(data, event_type):
            return True
        return self._event_hook_is_event_type(event_type) and self.is_external(data.get("model"))

    def is_external(self, model: str | None) -> bool:
        """True unless every deployment of the model group says it is hosted inside the deployment."""
        if not model:
            return True
        if model not in self._external:
            from litellm.proxy.proxy_server import llm_router

            deployments = (llm_router.get_model_list(model_name=model) or []) if llm_router else []
            locations = [(d.get("model_info") or {}).get("aihub_hosting_location") for d in deployments]
            self._external[model] = not locations or any(location != LOCAL_HOSTING for location in locations)
        return self._external[model]

    # ------------------------------------------------------------------ request

    @staticmethod
    def allow_list_pattern(words: list[str]) -> str | None:
        """One pattern that must match the whole span. Anchored with string anchors, not ^ and $: the analyzer matches
        with MULTILINE, so ^ and $ would let a span over a line break pass on its first line ("Sie" + "Anna Muster")."""
        words = [word.strip() for word in words if word and word.strip()]
        alternation = "|".join(re.escape(word) for word in words)
        return rf"\A(?:{alternation}){NUMBERED_LABEL_SUFFIX}\Z" if words else None

    async def analyze(self, text: str) -> list[dict]:
        request = {"text": text, "language": self.language, "entities": self.entities or None}
        if self.allow_list:
            request |= {"allow_list": [self.allow_list], "allow_list_match": "regex"}
        try:
            response = await self.client.post(self.analyze_url, headers={"Authorization": f"Bearer {self.api_key}"},
                                              json=request)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            logger.error("PII analysis failed, refusing the call: %s", error)
            raise AnonymisationUnavailableError(
                f"PII anonymisation is unavailable, so the request was not sent: {type(error).__name__}") from error

    @staticmethod
    def texts_of(message: dict) -> list[str]:
        content = message.get("content")
        if isinstance(content, str):
            return [content]
        if isinstance(content, list):
            return [p["text"] for p in content if isinstance(p, dict) and p.get("type") == "text" and p.get("text")]
        return []

    async def mask_message(self, message: dict, masker: PlaceholderMasker) -> None:
        content = message.get("content")
        if isinstance(content, str) and content:
            message["content"] = masker.mask(content, await self.analyze(content))
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                    part["text"] = masker.mask(part["text"], await self.analyze(part["text"]))

    async def async_pre_call_hook(self, user_api_key_dict: Any, cache: Any, data: dict, call_type: str) -> dict:
        if call_type not in CHAT_CALL_TYPES:
            return data
        messages = data.get("messages") or []
        reserved = {token for message in messages for text in self.texts_of(message) for token in TOKEN.findall(text)}
        masker = PlaceholderMasker(reserved)
        for message in messages:
            await self.mask_message(message, masker)
        response_format = data.get("response_format") or {}
        json_output = isinstance(response_format, dict) and response_format.get("type") in JSON_RESPONSE_FORMATS
        self._sweep()
        call_id = data.setdefault("litellm_call_id", str(uuid.uuid4()))
        self._maps[call_id] = (time.monotonic(), masker.tokens, json_output)
        return data

    # ------------------------------------------------------------------ response

    def _sweep(self) -> None:
        now = time.monotonic()
        for call_id in [k for k, (created, _, _) in self._maps.items() if now - created > MAP_TTL_SECONDS]:
            del self._maps[call_id]

    @staticmethod
    def json_escaped(tokens: dict[str, str]) -> dict[str, str]:
        return {token: json.dumps(value, ensure_ascii=False)[1:-1] for token, value in tokens.items()}

    async def async_post_call_success_hook(self, data: dict, user_api_key_dict: Any, response: Any) -> Any:
        if data.get("stream"):
            return response
        entry = self._maps.pop(data.get("litellm_call_id"), None)
        if entry is None:
            return response
        _, tokens, json_output = entry
        text = StreamRestorer(self.json_escaped(tokens) if json_output else tokens)
        args = StreamRestorer(self.json_escaped(tokens))
        for choice in getattr(response, "choices", None) or []:
            message = getattr(choice, "message", None)
            if message is None:
                continue
            for field in ("content", "reasoning_content"):
                if isinstance(getattr(message, field, None), str):
                    setattr(message, field, text.restore(getattr(message, field)))
            for tool_call in getattr(message, "tool_calls", None) or []:
                function = getattr(tool_call, "function", None)
                if function is not None and isinstance(function.arguments, str):
                    function.arguments = args.restore(function.arguments)
        return response

    async def async_post_call_failure_hook(self, request_data: dict, original_exception: Exception,
                                           user_api_key_dict: Any, traceback_str: str | None = None) -> None:
        self._maps.pop(request_data.get("litellm_call_id"), None)

    async def async_post_call_streaming_iterator_hook(self, user_api_key_dict: Any, response: Any,
                                                      request_data: dict) -> AsyncGenerator[Any, None]:
        entry = self._maps.get(request_data.get("litellm_call_id"))
        if entry is None:
            async for chunk in response:
                yield chunk
            return
        _, tokens, json_output = entry
        text_tokens, args_tokens = (self.json_escaped(tokens) if json_output else tokens), self.json_escaped(tokens)
        restorers: dict[tuple, StreamRestorer] = {}

        def restorer(key: tuple) -> StreamRestorer:
            if key not in restorers:
                restorers[key] = StreamRestorer(args_tokens if key[1] == "tool" else text_tokens)
            return restorers[key]

        last_chunk = None
        try:
            async for chunk in response:
                last_chunk = chunk
                for choice in getattr(chunk, "choices", None) or []:
                    index, delta = getattr(choice, "index", 0) or 0, getattr(choice, "delta", None)
                    if delta is None:
                        continue
                    for field in ("content", "reasoning_content"):
                        if getattr(delta, field, None):
                            setattr(delta, field, restorer((index, field)).feed(getattr(delta, field)))
                    for tool_call in getattr(delta, "tool_calls", None) or []:
                        function = getattr(tool_call, "function", None)
                        if function is not None and function.arguments:
                            key = (index, "tool", getattr(tool_call, "index", 0) or 0)
                            function.arguments = restorer(key).feed(function.arguments)
                    if getattr(choice, "finish_reason", None):
                        self._flush_into(delta, index, restorers)
                yield chunk
            pending = {key: r.flush() for key, r in restorers.items() if r.hold}
            if pending and last_chunk is not None:
                yield self._tail_chunk(last_chunk, pending)
        finally:
            self._maps.pop(request_data.get("litellm_call_id"), None)

    @staticmethod
    def _flush_into(delta: Any, index: int, restorers: dict[tuple, StreamRestorer]) -> None:
        """Release text held back for a finishing choice into the chunk that carries finish_reason."""
        for key, held in restorers.items():
            if key[0] != index or not held.hold:
                continue
            rest = held.flush()
            if key[1] == "tool":
                for tool_call in getattr(delta, "tool_calls", None) or []:
                    if (getattr(tool_call, "index", 0) or 0) == key[2] and tool_call.function is not None:
                        tool_call.function.arguments = (tool_call.function.arguments or "") + rest
                        break
                else:
                    held.hold = rest  # no tool-call delta in this chunk: goes out in the tail chunk
            else:
                setattr(delta, key[1], (getattr(delta, key[1], None) or "") + rest)

    @staticmethod
    def _tail_chunk(last_chunk: Any, pending: dict[tuple, str]) -> Any:
        tail = copy.deepcopy(last_chunk)
        for choice in tail.choices:
            index = getattr(choice, "index", 0) or 0
            choice.delta.content = pending.get((index, "content"), "")
            if hasattr(choice.delta, "reasoning_content"):
                choice.delta.reasoning_content = pending.get((index, "reasoning_content"))
            for tool_call in getattr(choice.delta, "tool_calls", None) or []:
                if tool_call.function is not None:
                    tool_call.function.arguments = pending.get((index, "tool", getattr(tool_call, "index", 0) or 0), "")
        return tail
