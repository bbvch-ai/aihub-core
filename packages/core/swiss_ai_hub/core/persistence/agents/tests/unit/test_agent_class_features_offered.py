"""Which chat toggles a profile shows: its blueprint's features, less those the profile switched off (#1568)."""

from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity


def _universal() -> AgentClassEntity:
    return AgentClassEntity.model_construct(
        agent_class="UniversalAgent",
        supported_features=["web_search", "code_interpreter"],
        feature_config_fields={"web_search": "web_search"},
    )


def test_a_profile_with_the_feature_configured_offers_it() -> None:
    offered = _universal().features_offered_by({"web_search": {"max_results": 5}})

    assert offered == ["code_interpreter", "web_search"]


def test_a_profile_with_the_feature_switched_off_does_not_offer_it() -> None:
    assert _universal().features_offered_by({"web_search": None}) == ["code_interpreter"]


def test_a_profile_saved_before_the_feature_existed_does_not_offer_it() -> None:
    assert _universal().features_offered_by({}) == ["code_interpreter"]


def test_a_feature_no_field_switches_is_always_offered() -> None:
    entity = AgentClassEntity.model_construct(agent_class="RAGAgent", supported_features=["user_files"])

    assert entity.features_offered_by({}) == ["user_files"]
