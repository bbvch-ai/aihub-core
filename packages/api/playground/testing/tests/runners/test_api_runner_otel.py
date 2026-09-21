from swiss_ai_hub.api.runners.api_runner import CAPTURED_REQUEST_HEADERS


def test_captured_request_headers_is_a_bounded_allowlist() -> None:
    """Regression guard for issue #1496: header capture must not be the catch-all [".*"].

    Capturing every header re-inflated trace/metric cardinality; the allowlist must stay
    small and explicit.
    """
    assert CAPTURED_REQUEST_HEADERS != [".*"]
    assert ".*" not in CAPTURED_REQUEST_HEADERS
    assert 0 < len(CAPTURED_REQUEST_HEADERS) <= 5
    assert all(isinstance(header, str) for header in CAPTURED_REQUEST_HEADERS)
