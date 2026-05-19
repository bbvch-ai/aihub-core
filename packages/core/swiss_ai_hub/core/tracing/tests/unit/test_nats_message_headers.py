from swiss_ai_hub.core.tracing import NATSMessageHeaders


class TestExtractAihubHeaders:
    """`extract_aihub_headers` is the single ingress where `X-AIHub-*` headers enter the agent
    pipeline (called from the API controller for HTTP and from both subscribers for NATS). It
    must filter to the prefix and normalize key casing so downstream consumers can read by a
    single canonical (lowercase) key regardless of how the originating client cased them."""

    def test_canonical_case_input_is_returned_lowercased(self):
        result = NATSMessageHeaders.extract_aihub_headers({"X-AIHub-User-Token": "tok"})
        assert result == {"x-aihub-user-token": "tok"}

    def test_already_lowercase_input_passes_through(self):
        # Production path: Starlette lowercases HTTP header names before our code sees them.
        result = NATSMessageHeaders.extract_aihub_headers({"x-aihub-user-token": "tok"})
        assert result == {"x-aihub-user-token": "tok"}

    def test_uppercase_input_is_returned_lowercased(self):
        result = NATSMessageHeaders.extract_aihub_headers({"X-AIHUB-USER-TOKEN": "tok"})
        assert result == {"x-aihub-user-token": "tok"}

    def test_non_aihub_headers_are_filtered_out(self):
        result = NATSMessageHeaders.extract_aihub_headers(
            {
                "Authorization": "Bearer secret",
                "Content-Type": "application/json",
                "X-AIHub-User-Token": "tok",
            }
        )
        assert result == {"x-aihub-user-token": "tok"}

    def test_multiple_aihub_headers_are_all_extracted(self):
        result = NATSMessageHeaders.extract_aihub_headers(
            {
                "X-AIHub-User-Token": "tok",
                "X-AIHub-On-Behalf-Of": "alice@example.com",
            }
        )
        assert result == {
            "x-aihub-user-token": "tok",
            "x-aihub-on-behalf-of": "alice@example.com",
        }

    def test_empty_input_returns_empty_dict(self):
        # Callers rely on this so they can unconditionally forward the result without a None check.
        assert NATSMessageHeaders.extract_aihub_headers({}) == {}

    def test_none_input_returns_empty_dict(self):
        assert NATSMessageHeaders.extract_aihub_headers(None) == {}

    def test_prefix_match_is_case_insensitive_but_value_is_preserved_verbatim(self):
        # Values must never be transformed — only keys are normalized. Tokens with mixed case or
        # special characters must round-trip exactly.
        result = NATSMessageHeaders.extract_aihub_headers({"x-aihub-user-token": "AbCd-1234_xyz"})
        assert result == {"x-aihub-user-token": "AbCd-1234_xyz"}


class TestWithAihubHeaders:
    """``with_aihub_headers`` is the egress where headers are placed onto the NATS envelope. It
    defensively filters by the ``X-AIHub-*`` prefix so a caller who accidentally passes a wider
    dict (e.g. raw request.headers) cannot leak ``Authorization``/``Cookie``/etc. to NATS."""

    def test_aihub_headers_are_merged_into_outgoing_headers(self):
        result = NATSMessageHeaders().with_aihub_headers({"X-AIHub-User-Token": "tok"}).to_dict()
        assert result == {"X-AIHub-User-Token": "tok"}

    def test_non_aihub_headers_are_dropped(self):
        """Defense in depth: any non-prefixed key must not reach NATS, even if the caller passes it."""
        result = (
            NATSMessageHeaders()
            .with_aihub_headers(
                {
                    "Authorization": "Bearer secret",
                    "Cookie": "session=abc",
                    "X-AIHub-User-Token": "tok",
                }
            )
            .to_dict()
        )
        assert result == {"X-AIHub-User-Token": "tok"}

    def test_prefix_match_is_case_insensitive(self):
        """Mirrors extract_aihub_headers — both sides of the contract treat the prefix the same way."""
        result = (
            NATSMessageHeaders().with_aihub_headers({"x-aihub-user-token": "tok", "X-AIHUB-TENANT": "acme"}).to_dict()
        )
        assert result == {"x-aihub-user-token": "tok", "X-AIHUB-TENANT": "acme"}

    def test_none_input_is_a_noop(self):
        result = NATSMessageHeaders().with_aihub_headers(None).to_dict()
        assert result == {}

    def test_empty_dict_input_is_a_noop(self):
        result = NATSMessageHeaders().with_aihub_headers({}).to_dict()
        assert result == {}

    def test_existing_headers_are_preserved(self):
        """Filtering must not wipe out other headers set by earlier builder calls (trace context, Nats-Msg-Id)."""
        result = (
            NATSMessageHeaders()
            .with_header("Nats-Msg-Id", "msg-123")
            .with_aihub_headers({"X-AIHub-User-Token": "tok", "Authorization": "should-drop"})
            .to_dict()
        )
        assert result == {"Nats-Msg-Id": "msg-123", "X-AIHub-User-Token": "tok"}
