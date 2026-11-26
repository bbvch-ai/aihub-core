"""Unit tests for the LiteLLM hook that books calls without a customer to `no-tenant`.

Not part of a CI `make test` scope. Run with the other LiteLLM function tests:

    uv run --with "litellm==1.106.4" pytest infra/deployment/templates/litellm_functions/test_tenant_attribution.py

What LiteLLM then writes to its spend tables was checked against a running v1.106.4 proxy (ADR 2026_11_09).
"""

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = Path(__file__).parent / "tenant_attribution.py"


def _load_module():
    sys.modules.pop("tenant_attribution", None)
    spec = importlib.util.spec_from_file_location("tenant_attribution", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call(end_user_id: str | None, metadata_field: str = "metadata"):
    key = SimpleNamespace(end_user_id=end_user_id)
    data = {"model": "m", metadata_field: {"user_api_key_end_user_id": end_user_id}}
    return key, data


def _run(key, data) -> dict:
    module = _load_module()
    return asyncio.run(module.TenantAttribution().async_pre_call_hook(key, None, data, "completion"))


def test_a_call_without_a_customer_is_booked_to_no_tenant():
    key, data = _call(None)

    data = _run(key, data)

    assert key.end_user_id == "no-tenant"
    assert data["metadata"]["user_api_key_end_user_id"] == "no-tenant"


def test_routes_that_keep_their_metadata_as_litellm_metadata_are_booked_too():
    key, data = _call(None, metadata_field="litellm_metadata")

    data = _run(key, data)

    assert data["litellm_metadata"]["user_api_key_end_user_id"] == "no-tenant"


def test_a_customer_the_caller_named_is_kept():
    key, data = _call("tenant-a")

    data = _run(key, data)

    assert key.end_user_id == "tenant-a"
    assert data["metadata"]["user_api_key_end_user_id"] == "tenant-a"


def test_the_id_matches_the_one_the_hub_sends():
    """The Hub's `LiteLLMCustomerService.NO_TENANT_CUSTOMER_ID`; both must name one customer line."""
    assert _load_module().NO_TENANT_CUSTOMER_ID == "no-tenant"
