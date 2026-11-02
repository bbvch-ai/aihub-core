from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from openai import APITimeoutError, BadRequestError
from swiss_ai_hub.core.imap import ParsedMessage

from swiss_ai_hub.agent.imap.mail_language_detector import MailLanguageDetector


def _message(body: str = "Where is bbv?") -> ParsedMessage:
    return ParsedMessage(message_id="1", sender="anna@test", subject="bbv locations", body_text=body)


def _llm_answering(*answers: str | Exception) -> MagicMock:
    responses = [
        answer if isinstance(answer, Exception) else MagicMock(message=MagicMock(content=answer)) for answer in answers
    ]
    return MagicMock(achat=AsyncMock(side_effect=responses))


def _bad_request() -> BadRequestError:
    request = httpx.Request("POST", "http://litellm/chat")
    return BadRequestError("chat_template is not supported", response=httpx.Response(400, request=request), body=None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("answer", "locale"),
    [("EN", "en"), ("DE", "de"), ("fr", "fr"), ("IT.", "it"), ("The email is German, not English.\nDE", "de")],
    ids=["english", "german", "lowercase", "trailing punctuation", "last label wins"],
)
async def test_the_detected_language_becomes_the_locale(answer: str, locale: str):
    assert await MailLanguageDetector.detect(_llm_answering(answer), _message()) == locale


@pytest.mark.asyncio
@pytest.mark.parametrize("answer", ["OTHER", "Vietnamese", ""], ids=["other", "unrecognised", "empty"])
async def test_a_language_without_a_locale_is_reported_as_unknown(answer: str):
    assert await MailLanguageDetector.detect(_llm_answering(answer), _message()) is None


@pytest.mark.asyncio
async def test_a_gateway_failure_is_reported_as_unknown_instead_of_failing_the_draft():
    request = httpx.Request("POST", "http://litellm/chat")

    assert await MailLanguageDetector.detect(_llm_answering(APITimeoutError(request=request)), _message()) is None


@pytest.mark.asyncio
async def test_a_model_rejecting_the_reasoning_switch_is_asked_again_without_it():
    llm = _llm_answering(_bad_request(), "EN")

    assert await MailLanguageDetector.detect(llm, _message()) == "en"
    assert "extra_body" in llm.achat.await_args_list[0].kwargs
    assert "extra_body" not in llm.achat.await_args_list[1].kwargs


@pytest.mark.asyncio
async def test_only_the_opening_of_a_long_body_is_sent():
    llm = _llm_answering("EN")

    await MailLanguageDetector.detect(llm, _message(body="Where is bbv? " + "x" * 10_000))

    prompt = llm.achat.await_args.args[0][0].content
    assert "Where is bbv?" in prompt
    assert len(prompt) < 3_000


@pytest.mark.parametrize(
    ("locale", "language", "salutation"),
    [("en", "English", "Dear Mr Smith"), ("de", "German", "Guten Tag Herr Muster"), ("fr", "French", "Bonjour")],
)
def test_the_reply_language_leads_the_drafting_prompt(locale: str, language: str, salutation: str):
    prompt = MailLanguageDetector.with_reply_language(
        "Antworte formell. Anrede: Guten Tag Frau/Herr [Nachname].", locale
    )

    directive, rest = prompt.split("\n\n", 1)
    assert directive.startswith(f"REPLY LANGUAGE: {language}.")
    assert salutation in directive
    assert rest == "Antworte formell. Anrede: Guten Tag Frau/Herr [Nachname]."
