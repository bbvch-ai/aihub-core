"""Covers the ceiling a newly created tenant starts with.

The rule grammar is additive only, so "every model except X" has to be expressed by enumerating the
survivors. That makes the derivation the only thing standing between an excluded model and every new
tenant, and the reason these assertions check the resolved ``AccessChecker`` verdict rather than just
the emitted strings.
"""

import httpx
import pytest
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker

from swiss_ai_hub.api.routes.access.access_capability_service import AccessCapabilityService
from swiss_ai_hub.api.routes.access.default_tenant_access_rules_service import (
    KNOWN_RULE_FAMILIES,
    DefaultTenantAccessRulesService,
)
from swiss_ai_hub.api.routes.access.model_roster_unavailable_error import ModelRosterUnavailableError

_EXCLUDED = "text-generation/Apertus-70B-Instruct-2509"

_CPU_ROSTER = {
    "text-generation": [
        "Apertus-70B-Instruct-2509",
        "gemma-4-31B-it",
        "Kimi-K2.6",
        "Ministral-3-14B-Instruct-2512",
        "Qwen3.5-122B-A10B-FP8",
        "MinerU2.5-2509-1.2B",
    ],
    "embedding": ["bge-m3"],
    "reranker": ["bge"],
    "transcription": ["whisper-large-v3"],
    "image-generation": ["flux"],
}

# A GPU deployment serves an entirely different roster — no cloud chat models, no flux, and its own
# transcription model. A hardcoded default would leave such a tenant with no chat model at all.
_GPU_ROSTER = {
    "text-generation": ["Qwen3-VL-30B-A3B-Instruct-FP8", "MinerU2.5-2509-1.2B"],
    "embedding": ["bge-m3"],
    "reranker": ["bge"],
    "transcription": ["faster-whisper-large-v3"],
}


@pytest.fixture(autouse=True)
def _exclude_apertus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIHUB_TENANT_DEFAULT_ACCESS_EXCLUDED_MODELS", _EXCLUDED)


def _stub_roster(monkeypatch: pytest.MonkeyPatch, roster: dict[str, list[str]]) -> None:
    async def _roster() -> dict[str, list[str]]:
        return roster

    monkeypatch.setattr(AccessCapabilityService, "available_models_by_capability", _roster)


def _checker(rules: list[str]) -> AccessChecker:
    """Resolves against the broadest seeded role, so anything denied is denied by the ceiling alone."""
    return AccessChecker(user_access_rules=["aihub.admin.>"], tenant_access_rules=rules)


@pytest.mark.asyncio
async def test_excluded_model_is_denied_and_its_siblings_are_not(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_roster(monkeypatch, _CPU_ROSTER)

    checker = _checker(await DefaultTenantAccessRulesService.derive())

    assert not checker.has_access_to_model("text-generation", "Apertus-70B-Instruct-2509")
    for survivor in ("gemma-4-31B-it", "Kimi-K2.6", "Ministral-3-14B-Instruct-2512", "Qwen3.5-122B-A10B-FP8"):
        assert checker.has_access_to_model("text-generation", survivor), survivor


@pytest.mark.asyncio
async def test_capability_without_exclusions_collapses_to_a_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    """A wildcard is what lets a model added to that capability later reach new tenants unattended."""
    _stub_roster(monkeypatch, _CPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()

    assert "aihub.user.model.embedding.>" in rules
    assert _checker(rules).has_access_to_model("embedding", "a-model-added-tomorrow")


@pytest.mark.asyncio
async def test_excluded_capability_is_enumerated_not_wildcarded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The enumeration is also what makes each chat model an individually toggleable row in the editor."""
    _stub_roster(monkeypatch, _CPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()

    assert "aihub.user.model.text-generation.>" not in rules
    assert not _checker(rules).has_access_to_model("text-generation", "a-model-added-tomorrow")


@pytest.mark.asyncio
async def test_gpu_roster_still_yields_a_usable_chat_model(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_roster(monkeypatch, _GPU_ROSTER)

    checker = _checker(await DefaultTenantAccessRulesService.derive())

    assert checker.has_access_to_model("text-generation", "Qwen3-VL-30B-A3B-Instruct-FP8")
    assert checker.has_access_to_model("transcription", "faster-whisper-large-v3")


@pytest.mark.asyncio
async def test_non_model_families_stay_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ceiling caps every family, so a model-only ceiling would silently lock the tenant out."""
    _stub_roster(monkeypatch, _CPU_ROSTER)

    checker = _checker(await DefaultTenantAccessRulesService.derive())

    assert checker.has_access_to_agent("RAGAgent", "shared-knowledge-rag")
    assert checker.has_access_to_process("SomeProcess", "some-id")
    assert checker.has_access_to_service("model")


@pytest.mark.asyncio
async def test_every_emitted_rule_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_roster(monkeypatch, _CPU_ROSTER)

    for rule in await DefaultTenantAccessRulesService.derive():
        assert AccessChecker.validate_user_access_rule(rule), rule


@pytest.mark.asyncio
async def test_exclusion_absent_from_the_roster_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """A CPU-only exclusion is legitimate on a GPU instance, so it must not fail the derivation."""
    _stub_roster(monkeypatch, _GPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()

    assert "aihub.user.model.text-generation.>" in rules


@pytest.mark.asyncio
async def test_unreachable_gateway_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _boom() -> dict[str, list[str]]:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(AccessCapabilityService, "available_models_by_capability", _boom)

    with pytest.raises(ModelRosterUnavailableError):
        await DefaultTenantAccessRulesService.derive()


@pytest.mark.asyncio
async def test_empty_roster_raises_rather_than_seeding_a_model_less_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_roster(monkeypatch, {})

    with pytest.raises(ModelRosterUnavailableError):
        await DefaultTenantAccessRulesService.derive()


@pytest.mark.asyncio
async def test_every_known_rule_family_is_covered(monkeypatch: pytest.MonkeyPatch) -> None:
    """A seventh family added to the platform would otherwise be silently absent from every new tenant's
    ceiling — denied by omission, with nothing failing to say so."""
    _stub_roster(monkeypatch, _CPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()
    covered = {rule.removeprefix("aihub.user.").removeprefix("aihub.admin.").split(".")[0] for rule in rules}

    assert covered == KNOWN_RULE_FAMILIES
