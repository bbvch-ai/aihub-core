from unittest.mock import Mock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ImageBlock, TextBlock

from swiss_ai_hub.core.generative_ai.resources.models.llm.stored_image_signer import StoredImageSigner

REFERENCE = "s3://agent-files/Universal/a1/images/abc.png"


@pytest.fixture
def service() -> Mock:
    service = Mock()
    service.generate_sas_url.side_effect = lambda bucket, key, **_: f"https://storage/{bucket}/{key}?signed"
    with patch.object(StoredImageSigner, "_service", return_value=service):
        yield service


def test_a_stored_image_is_signed_and_the_original_message_is_kept(service: Mock):
    messages = [ChatMessage(role="user", blocks=[TextBlock(text="What is this?"), ImageBlock(url=REFERENCE)])]

    signed = StoredImageSigner.signed(messages)

    assert str(signed[0].blocks[1].url) == "https://storage/agent-files/Universal/a1/images/abc.png?signed"
    assert signed[0].blocks[0].text == "What is this?"
    assert str(messages[0].blocks[1].url) == REFERENCE


@pytest.mark.parametrize("inline", [True, False])
def test_the_signature_targets_the_endpoint_the_inlining_needs(service: Mock, monkeypatch: pytest.MonkeyPatch, inline):
    monkeypatch.setenv("RAG_IMAGE_INLINE_ENABLED", str(inline).lower())

    StoredImageSigner.signed([ChatMessage(role="user", blocks=[ImageBlock(url=REFERENCE)])])

    assert service.generate_sas_url.call_args.kwargs["internal"] is inline


def test_messages_without_stored_images_are_passed_through(service: Mock):
    messages = [ChatMessage(role="user", blocks=[ImageBlock(url="https://example.com/a.png")])]

    assert StoredImageSigner.signed(messages) is messages
    service.generate_sas_url.assert_not_called()
