import pytest

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker

_FULL_TENANT_ACCESS = ["aihub.admin.>"]


def _checker(user_rules: list[str], tenant_rules: list[str] | None = None) -> AccessChecker:
    return AccessChecker(user_rules, tenant_access_rules=tenant_rules or _FULL_TENANT_ACCESS)


def test_model_user_rule_builds_canonical_rule() -> None:
    assert AccessChecker.model_user_rule("text-generation", "gpt-4o") == "aihub.user.model.text-generation.gpt-4o"


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("gpt-4o", "gpt-4o"),
        ("gpt-4.1", "gpt-4_1"),
        ("claude-3.5-sonnet", "claude-3_5-sonnet"),
        ("text-generation/gpt-4", "text-generation_gpt-4"),
        ("model:v1", "model_v1"),
        ("under_score", "under_score"),
    ],
)
def test_normalize_model_segment_collapses_to_single_segment(raw: str, normalized: str) -> None:
    """Dots, slashes and colons must not survive as extra hierarchy levels or invalid tokens."""
    assert AccessChecker._normalize_model_segment(raw) == normalized
    # The normalized segment must contain no separator that the matcher splits on.
    assert "." not in AccessChecker.model_user_rule("text-generation", raw).rsplit(".", 1)[-1]


@pytest.mark.parametrize(
    "model_name",
    [
        "gpt-4o",
        "gpt-4.1",
        "claude-3.5-sonnet",
        "text-generation/gpt-4",
        "gemini-1.5-pro",
        "model:v1",
    ],
)
def test_capability_wildcard_grant_covers_any_model_name(model_name: str) -> None:
    """A per-capability grant must reach every model of that capability, regardless of name characters."""
    checker = _checker(["aihub.user.model.text-generation.*"])
    assert checker.has_access_to_model("text-generation", model_name) is True


def test_capability_grant_does_not_leak_across_capabilities() -> None:
    checker = _checker(["aihub.user.model.text-generation.*"])
    assert checker.has_access_to_model("embedding", "text-embedding-3-large") is False


def test_concrete_model_grant_is_scoped_to_that_model() -> None:
    grant = [AccessChecker.model_user_rule("text-generation", "gpt-4.1")]
    checker = _checker(grant)
    assert checker.has_access_to_model("text-generation", "gpt-4.1") is True
    assert checker.has_access_to_model("text-generation", "gpt-4o") is False


def test_no_grant_denies_access() -> None:
    checker = _checker(["aihub.user.agent.>"])
    assert checker.has_access_to_model("text-generation", "gpt-4o") is False


def test_tenant_ceiling_caps_model_access() -> None:
    checker = _checker(["aihub.user.model.>"], tenant_rules=["aihub.user.model.embedding.*"])
    assert checker.has_access_to_model("embedding", "text-embedding-3-large") is True
    assert checker.has_access_to_model("text-generation", "gpt-4o") is False


@pytest.mark.parametrize(
    ("capability", "expected"),
    [("text-generation", True), ("embedding", False)],
)
def test_has_access_to_model_capability(capability: str, expected: bool) -> None:
    checker = _checker(["aihub.user.model.text-generation.*"])
    assert checker.has_access_to_model_capability(capability) is expected


def test_sysadmin_has_access_to_every_model() -> None:
    checker = AccessChecker(user_access_rules=[], tenant_access_rules=[], is_sys_admin=True)
    assert checker.has_access_to_model("text-generation", "gpt-4.1") is True
    assert checker.has_access_to_model_capability("embedding") is True


def test_normalization_collision_is_accepted_tradeoff() -> None:
    """Names differing only by separator collapse to the same rule — documented, accepted behaviour."""
    assert AccessChecker.model_user_rule("text-generation", "gpt-4.1") == AccessChecker.model_user_rule(
        "text-generation", "gpt-4_1"
    )
