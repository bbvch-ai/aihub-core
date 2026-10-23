import email
from datetime import UTC, datetime
from email.policy import default as default_policy

from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.imap import DraftEmailSettings, ParsedMessage

from swiss_ai_hub.agent.imap.quoted_original import QuotedOriginal
from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer


def _parsed(**overrides) -> ParsedMessage:
    base = {
        "message_id": "101",
        "sender": "Alice <alice@example.com>",
        "subject": "Quarterly report",
        "body_text": "Please review the attached numbers.",
        "rfc_message_id": "<orig-123@example.com>",
    }
    base.update(overrides)
    return ParsedMessage(**base)


def _parse(raw: bytes):
    return email.message_from_bytes(raw, policy=default_policy)


def test_compose_from_parsed_sets_threading_headers_and_returns_envelope():
    composed = ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body="Thanks, looks good.")
    message = _parse(composed.raw)

    assert message["From"] == "me@example.com"
    assert message["To"] == "Alice <alice@example.com>"
    assert message["Subject"] == "Re: Quarterly report"
    assert message["In-Reply-To"] == "<orig-123@example.com>"
    assert message["References"] == "<orig-123@example.com>"
    assert message.get_body(("plain",)).get_content().strip() == "Thanks, looks good."

    # The returned envelope mirrors the composed headers, so the persisted ref never drifts from the draft.
    assert composed.subject == "Re: Quarterly report"
    assert composed.recipient == "Alice <alice@example.com>"
    assert composed.in_reply_to == "<orig-123@example.com>"


def test_compose_from_parsed_prefers_reply_to_over_sender():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(reply_to="desk@example.com"), from_address="me@example.com", body="ok"
    )

    assert composed.recipient == "desk@example.com"
    assert _parse(composed.raw)["To"] == "desk@example.com"


def test_reply_subject_is_idempotent():
    assert ReplyComposer.reply_subject("Re: Already replied") == "Re: Already replied"
    assert ReplyComposer.reply_subject("re: lowercase") == "re: lowercase"
    assert ReplyComposer.reply_subject("Fresh topic") == "Re: Fresh topic"


def test_references_chain_appends_original_message_id():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(references="<a@x> <b@x>"), from_address="me@example.com", body="ok"
    )

    assert _parse(composed.raw)["References"] == "<a@x> <b@x> <orig-123@example.com>"


def _plain(composed) -> str:
    return _parse(composed.raw).get_body(("plain",)).get_content()


def _html(composed) -> str:
    return _parse(composed.raw).get_body(("html",)).get_content()


def test_draft_carries_an_html_part_with_a_plain_text_alternative():
    composed = ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body="**Thanks**")

    assert _parse(composed.raw).get_content_type() == "multipart/alternative"
    assert "<strong>Thanks</strong>" in _html(composed)
    assert _plain(composed).strip() == "Thanks"


def test_highlight_renders_as_an_inline_yellow_background_and_leaves_no_markers():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(), from_address="me@example.com", body="Note: ==the deadline is Friday==."
    )

    assert '<span style="background-color:#ffff00">the deadline is Friday</span>' in _html(composed)
    assert "<mark>" not in _html(composed)
    assert _plain(composed).strip() == "Note: the deadline is Friday."


def test_html_in_the_model_output_is_shown_as_text_never_parsed():
    body = (
        'Hi <script>alert(1)</script><img src="https://tracker.example/p.gif"> <b onclick="x()">ok</b> '
        "[x](javascript:alert(1))"
    )

    html = _html(ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body=body))

    for tag in ("<script", "<img", "<b ", "<b>"):
        assert tag not in html
    assert "&lt;script&gt;" in html
    assert 'href="javascript' not in html


def test_angle_bracket_placeholder_survives_in_both_parts():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(), from_address="me@example.com", body="Freundliche Grüsse\n<Ihr Name>"
    )

    assert "&lt;Ihr Name&gt;" in _html(composed)
    assert _plain(composed).strip() == "Freundliche Grüsse\n<Ihr Name>"


def test_a_stray_angle_bracket_does_not_format_the_rest_of_the_reply():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(), from_address="me@example.com", body="Compare a<b and c>d.\n\nSecond paragraph."
    )

    assert "<b>" not in _html(composed)
    assert "<p>Second paragraph.</p>" in _html(composed)
    assert _plain(composed).strip() == "Compare a<b and c>d.\n\nSecond paragraph."


def test_plain_text_keeps_addresses_and_link_targets():
    body = "Contact Alice <alice@example.com>, see <https://example.com> or [the docs](https://example.com/d?a=1&b=2)."

    plain = _plain(ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body=body))

    assert plain.strip() == (
        "Contact Alice alice@example.com, see https://example.com or the docs <https://example.com/d?a=1&b=2>."
    )


def test_plain_text_keeps_list_markers_and_numbers():
    body = "- one\n- two\n    - nested\n- three\n\n1. first\n2. second"

    plain = _plain(ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body=body))

    assert plain.strip() == "- one\n- two\n   - nested\n- three\n\n1. first\n2. second"


def test_a_numbered_list_keeps_its_start_number_in_both_parts():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(), from_address="me@example.com", body="Steps:\n\n3. connect\n4. sign in"
    )

    assert '<ol start="3">' in _html(composed)
    assert _plain(composed).strip() == "Steps:\n\n3. connect\n4. sign in"


def test_a_paragraph_opening_with_a_date_keeps_its_number():
    plain = _plain(
        ReplyComposer.compose_from_parsed(
            _parsed(), from_address="me@example.com", body="Guten Tag\n\n31. Oktober ist der Stichtag."
        )
    )

    assert plain.strip() == "Guten Tag\n\n31. Oktober ist der Stichtag."


def test_bare_urls_become_links_without_repeating_the_address_in_plain_text():
    body = "See https://sgum-ssum.ch/veranstaltungen/kursauswahl/ and www.sgum.ch."

    composed = ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body=body)

    html = _html(composed)
    assert '<a href="https://sgum-ssum.ch/veranstaltungen/kursauswahl/"' in html
    assert '<a href="https://www.sgum.ch"' in html
    assert _plain(composed).strip() == body


def test_a_file_name_ending_in_a_country_code_is_not_a_link():
    html = _html(
        ReplyComposer.compose_from_parsed(
            _parsed(), from_address="me@example.com", body="Attach bericht.py, as on sgum.ch."
        )
    )

    assert "<a " not in html


def test_double_equals_inside_words_is_not_a_highlight():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(), from_address="me@example.com", body="Set status==active and mode==test."
    )

    assert "background-color" not in _html(composed)
    assert _plain(composed).strip() == "Set status==active and mode==test."


def test_highlight_markers_in_a_code_span_stay_literal():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(), from_address="me@example.com", body="Use `==literal==` in the config."
    )

    assert "<code>==literal==</code>" in _html(composed)
    assert "mark" not in _html(composed)


def test_highlight_may_wrap_other_formatting():
    html = _html(
        ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body="==**bold** inside==!")
    )

    assert '<span style="background-color:#ffff00"><strong>bold</strong> inside</span>!' in html


def test_without_a_quote_the_draft_contains_only_the_reply():
    composed = ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body="Thanks.")

    assert "Please review the attached numbers." not in _plain(composed)
    assert "Please review the attached numbers." not in _html(composed)


def test_quote_is_built_only_when_the_toggle_is_on():
    assert QuotedOriginal.for_draft(_parsed(), DraftEmailSettings()) is None
    assert QuotedOriginal.for_draft(_parsed(), DraftEmailSettings(quote_original=True)) is not None


def test_quote_labels_follow_the_profile_quote_language():
    quoted = QuotedOriginal.for_draft(_parsed(), DraftEmailSettings(quote_original=True, quote_locale="fr"))

    assert quoted is not None
    assert "De: Alice <alice@example.com>" in quoted.text


def test_quoted_original_follows_the_reply_with_its_header_block():
    parsed = _parsed(to="support@example.com", date=datetime(2026, 10, 22, 9, 5, tzinfo=UTC))
    quoted = QuotedOriginal.from_parsed(parsed, LocaleHandler("de"))

    composed = ReplyComposer.compose_from_parsed(parsed, from_address="me@example.com", body="Danke.", quoted=quoted)

    plain = _plain(composed)
    assert plain.index("Danke.") < plain.index("Von: Alice <alice@example.com>")
    for line in ("Gesendet: 22.10.2026 09:05", "An: support@example.com", "Betreff: Quarterly report"):
        assert line in plain
    assert "Cc:" not in plain, "a header the original lacks leaves no empty line"
    assert plain.rstrip().endswith("Please review the attached numbers.")
    assert "<b>Von:</b> Alice &lt;alice@example.com&gt;" in _html(composed)


def test_quoted_html_original_is_sanitised_and_drops_images():
    original_html = (
        "<html><head><title>Ignored</title><style>p{}</style></head><body>"
        '<p style="color:#333;position:fixed">Hello</p><img src="cid:logo"><img src="https://tracker.example/p.gif">'
        "<script>alert(1)</script><table><tr><td>cell</td></tr></table></body></html>"
    )
    quoted = QuotedOriginal.from_parsed(_parsed(body_html=original_html), LocaleHandler("en"))

    assert '<p style="color:#333">Hello</p>' in quoted.html
    assert "<td>cell</td>" in quoted.html
    for unsafe in ("<img", "<script", "alert(1)", "position", "Ignored"):
        assert unsafe not in quoted.html


def test_quoted_original_falls_back_to_text_derived_from_html_when_there_is_no_text_body():
    quoted = QuotedOriginal.from_parsed(
        _parsed(body_text=None, body_html="<p>First &amp; foremost</p><p>Second</p>"), LocaleHandler("en")
    )

    assert quoted.text.endswith("First & foremost\n\nSecond")


def test_plain_text_original_is_escaped_in_the_html_quote():
    quoted = QuotedOriginal.from_parsed(_parsed(body_text="a <b>not bold</b>\nline"), LocaleHandler("en"))

    assert "a &lt;b&gt;not bold&lt;/b&gt;<br>" in quoted.html
