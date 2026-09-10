import asyncio
from email.message import EmailMessage

import pytest

from swiss_ai_hub.core.generative_ai.document.loaders.eml_loader import EmlLoader

_SUBJECT = "Rechnung 2026-0042 Balmer Etienne AG"


def _mail(html: bool = False, attach: bool = False, both: bool = False) -> bytes:
    message = EmailMessage()
    message["Subject"] = _SUBJECT
    message["From"] = "buchhaltung@example.ch"
    message["Date"] = "Wed, 10 Sep 2026 09:14:00 +0200"
    if html and not both:
        message.set_content("<html><body><h2>Rechnung</h2><p>Betrag: <b>CHF 4250</b></p></body></html>", subtype="html")
    else:
        message.set_content("Die Lieferung erfolgte am 12. Maerz.")
        if both:
            message.add_alternative("<html><body><p>HTML rendering</p></body></html>", subtype="html")
    if attach:
        message.add_attachment(b"%PDF-1.4 " + b"X" * 4096, maintype="application", subtype="pdf", filename="beleg.pdf")
    return message.as_bytes()


def _load(raw: bytes) -> str:
    documents = asyncio.run(EmlLoader().aload_data_from_bytes(content=raw, filename="anfrage.eml"))
    return documents[0].text


def test_subject_becomes_the_heading():
    assert _load(_mail()).startswith(f"# {_SUBJECT}")


def test_plain_body_is_the_content():
    assert "Die Lieferung erfolgte am 12. Maerz." in _load(_mail())


def test_headers_do_not_leak_into_the_content():
    """The failure mode that makes MarkItDownLoader unusable for `.eml`."""
    text = _load(_mail(attach=True))
    assert "Content-Transfer-Encoding" not in text
    assert "MIME-Version" not in text
    assert "--===" not in text


def test_attachment_bytes_never_reach_the_content():
    text = _load(_mail(attach=True))
    assert "JVBERi" not in text and "WFhY" not in text


def test_attachment_filename_is_listed():
    assert "beleg.pdf" in _load(_mail(attach=True))


def test_html_only_body_is_converted_to_markdown():
    text = _load(_mail(html=True))
    assert "## Rechnung" in text
    assert "**CHF 4250**" in text
    assert "<p>" not in text


def test_plain_text_is_preferred_over_the_html_alternative():
    text = _load(_mail(both=True))
    assert "Die Lieferung erfolgte am 12. Maerz." in text
    assert "HTML rendering" not in text


def test_subject_is_published_in_metadata():
    documents = asyncio.run(EmlLoader().aload_data_from_bytes(content=_mail(), filename="anfrage.eml"))
    assert documents[0].metadata["subject"] == _SUBJECT


def test_no_page_count_is_invented_for_a_mail():
    documents = asyncio.run(EmlLoader().aload_data_from_bytes(content=_mail(), filename="anfrage.eml"))
    assert "number_of_pages" not in documents[0].metadata


def test_sync_load_data_refuses():
    with pytest.raises(RuntimeError):
        EmlLoader().load_data("anfrage.eml")
