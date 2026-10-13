"""Covers the ceiling a newly created tenant starts with.

The rule grammar is additive only, so "every model except X" has to be expressed by enumerating the
survivors. That makes the derivation the only thing standing between an excluded model and every new
tenant, and the reason these assertions check the resolved ``AccessChecker`` verdict rather than just
the emitted strings.
"""

import httpx
import pytest
from fastapi.routing import APIRoute
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker

from swiss_ai_hub.api.routes.access.access_capability_service import AccessCapabilityService
from swiss_ai_hub.api.routes.access.default_tenant_access_rules_service import DefaultTenantAccessRulesService
from swiss_ai_hub.api.routes.access.model_roster_unavailable_error import ModelRosterUnavailableError

_EXCLUDED = "text-generation/Apertus-70B-Instruct-2509"

_STANDARD_CLASS = "RAGAgent"
_NON_STANDARD_CLASS = "ExpertRAGAgent"

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

    # A standard blueprint: the agent family is curated rather than wildcarded, so only these reach it —
    # and only as far as the blueprint. Its existing profiles are deliberately not reachable; see
    # test_a_standard_blueprint_does_not_carry_its_existing_profiles.
    assert checker.has_access_to_agent_class(_STANDARD_CLASS)
    assert checker.has_access_to_process("SomeProcess", "some-id")
    assert checker.has_access_to_service("model")
    # The knowledge root: creating a database is guarded on the bare rule, and it is also what keeps the
    # knowledge page reachable while the tenant has no database of its own yet.
    assert checker.has_access("aihub.admin.knowledge")
    assert checker.has_access("aihub.user.knowledge.?>")


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


class _DummyPathParams(dict):
    """Fills a guard template's ``{path_params}`` with any concrete value — which segment a rule names
    is irrelevant here, only how many segments deep the guard sits.

    ``agent_class`` is the one exception. Agents are curated, so the ceiling names the standard classes
    instead of wildcarding the family, and probing with an arbitrary class would assert the opposite of
    what curation is for. Substituting a granted class keeps this test measuring depth, which is its job;
    that a non-standard class is denied at the same guards is asserted separately below.
    """

    def __missing__(self, key: str) -> str:
        if key == "agent_class":
            return _STANDARD_CLASS
        return "probe"


@pytest.mark.asyncio
async def test_the_derived_ceiling_permits_every_route_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """The ceiling caps every role, so a guard it cannot grant is unreachable for the whole tenant — and
    ``_capability_for_guard`` hides such a row rather than reporting it, making the failure silent.

    Read off the real mounted routes rather than a hand-kept list, because the gap this replaces was not a
    missing *family* but a missing *depth*: ``aihub.admin.knowledge.>`` never matches the bare
    ``aihub.admin.knowledge`` root that creating a database is guarded on, yet reports its family covered.
    """
    from app.main import runner

    _stub_roster(monkeypatch, _CPU_ROSTER)
    checker = _checker(await DefaultTenantAccessRulesService.derive())

    templates = {
        template
        for controller in runner.controllers
        for route in controller.router.routes
        if isinstance(route, APIRoute) and (template := AccessCapabilityService._route_template(route)) is not None
    }
    # Per-profile agent guards and per-database knowledge guards are the depths the ceiling deliberately does
    # not reach. Neither collection has a tenant column, so naming the whole subtree would hand the tenant
    # every profile or database in the deployment. ``AgentService._grant_instance_access`` and
    # ``KnowledgeService._grant_knowledge_access`` grant each resource to the tenant that creates it, which
    # is what covers these depths afterwards.
    guards = {
        template.format_map(_DummyPathParams())
        for template in templates
        if "{agent_id}" not in template and "{database}" not in template
    }

    assert guards, "no route guards discovered — the closure walk broke, not the ceiling"
    for guard in sorted(guards):
        assert checker.has_access(guard), guard


@pytest.mark.asyncio
async def test_only_the_standard_blueprints_reach_a_new_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enumerating the standard classes is what hides the rest — and what makes each an unticked,
    grantable row in the sysadmin's tenant-ceiling editor rather than a locked one."""
    _stub_roster(monkeypatch, _CPU_ROSTER)

    checker = _checker(await DefaultTenantAccessRulesService.derive())

    for standard in ("LLMWrappingAgent", "FewShotAgent", "RAGAgent"):
        assert checker.has_access_to_agent_class(standard), standard
    for withheld in (_NON_STANDARD_CLASS, "EmailClassificationAgent", "ConditionalAgent"):
        assert not checker.has_access_to_agent_class(withheld), withheld


@pytest.mark.asyncio
async def test_a_standard_blueprint_does_not_carry_its_existing_profiles(monkeypatch: pytest.MonkeyPatch) -> None:
    """The regression guard for aihub-core-private#257.

    Profiles live in one global collection with no tenant column, so ``aihub.admin.agent.<Class>.>`` would
    not mean "this tenant's profiles of this blueprint" — it would mean every profile of it in the
    deployment. A new tenant was therefore created already holding assistants other tenants had built.
    """
    _stub_roster(monkeypatch, _CPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()
    checker = _checker(rules)

    assert f"aihub.admin.agent.{_STANDARD_CLASS}.>" not in rules
    assert not checker.has_access_to_agent(_STANDARD_CLASS, "shared-knowledge-rag")
    # Creating one is still permitted — that is the whole point of keeping the bare root.
    assert checker.has_access(f"aihub.admin.agent.{_STANDARD_CLASS}")


@pytest.mark.asyncio
async def test_a_profile_the_tenant_creates_becomes_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The other half of the contract: the depth the ceiling no longer covers is covered per profile by
    ``AgentService._grant_instance_access``, so a tenant reaches what it built and nothing else."""
    _stub_roster(monkeypatch, _CPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()
    rules.append(AccessChecker.agent_instance_admin_rule(_STANDARD_CLASS, "our-own-profile"))
    checker = _checker(rules)

    assert checker.has_access_to_agent(_STANDARD_CLASS, "our-own-profile")
    assert not checker.has_access_to_agent(_STANDARD_CLASS, "someone-elses-profile")


@pytest.mark.asyncio
async def test_a_new_tenant_carries_no_existing_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """The regression guard for aihub-core-private#269.

    Databases live in one global collection with no tenant column, so ``aihub.admin.knowledge.>`` would not
    mean "this tenant's databases" — it would mean every database in the deployment. Admin access also
    implies use, so a new tenant's users could read and search what other tenants had ingested.
    """
    _stub_roster(monkeypatch, _CPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()
    checker = _checker(rules)

    assert "aihub.admin.knowledge.>" not in rules
    assert not checker.has_access("aihub.user.knowledge.other-tenants-db.policies")
    assert not checker.has_access("aihub.admin.knowledge.other-tenants-db")
    # Creating one is still permitted — that is the whole point of keeping the bare root.
    assert checker.has_access("aihub.admin.knowledge")


@pytest.mark.asyncio
async def test_a_database_the_tenant_creates_becomes_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The other half of the contract: ``KnowledgeService._grant_knowledge_access`` grants the new
    database's root and subtree to the creating tenant. The subtree is what reaches a namespace a pipeline
    creates later, which is granted to no one when it appears."""
    from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

    _stub_roster(monkeypatch, _CPU_ROSTER)

    rules = await DefaultTenantAccessRulesService.derive()
    rules.extend(KnowledgeService._database_admin_rules("our-own-db"))
    checker = _checker(rules)

    assert checker.has_access("aihub.admin.knowledge.our-own-db")
    assert checker.has_access("aihub.admin.knowledge.our-own-db.synced-folder")
    assert checker.has_access_to_knowledge_namespace("our-own-db", "synced-folder")
    assert checker.has_access_to_all_knowledge_namespaces("our-own-db")
    assert not checker.has_access_to_knowledge_namespace("other-tenants-db", "policies")


@pytest.mark.asyncio
async def test_a_withheld_blueprint_cannot_be_instantiated(monkeypatch: pytest.MonkeyPatch) -> None:
    """The companion to test_the_derived_ceiling_permits_every_route_guard: that one substitutes a
    granted class into every guard, so without this the denial side would go unasserted."""
    _stub_roster(monkeypatch, _CPU_ROSTER)

    checker = _checker(await DefaultTenantAccessRulesService.derive())

    assert not checker.has_access(f"aihub.admin.agent.{_NON_STANDARD_CLASS}")
    assert checker.has_access(f"aihub.admin.agent.{_STANDARD_CLASS}")


@pytest.mark.asyncio
async def test_the_standard_blueprint_list_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment that ships a different standard set says so here rather than in code."""
    monkeypatch.setenv("AIHUB_TENANT_DEFAULT_ACCESS_AGENT_CLASSES", f"{_NON_STANDARD_CLASS},RAGAgent")
    _stub_roster(monkeypatch, _CPU_ROSTER)

    checker = _checker(await DefaultTenantAccessRulesService.derive())

    assert checker.has_access_to_agent_class(_NON_STANDARD_CLASS)
    assert not checker.has_access_to_agent_class("LLMWrappingAgent")


@pytest.mark.asyncio
async def test_agent_rules_do_not_depend_on_the_class_roster(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reason this is an allow list and not an exclusion: the startup tenant is seeded at API boot,
    before any agent has answered discovery, so nothing can be derived from what is running."""
    monkeypatch.setattr(
        "swiss_ai_hub.core.persistence.agents.AgentClassEntity.get_all", staticmethod(lambda: []), raising=False
    )
    _stub_roster(monkeypatch, _CPU_ROSTER)

    checker = _checker(await DefaultTenantAccessRulesService.derive())

    assert checker.has_access_to_agent_class(_STANDARD_CLASS)
