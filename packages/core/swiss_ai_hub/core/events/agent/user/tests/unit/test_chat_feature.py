from swiss_ai_hub.core.events.agent.user.chat_feature import ChatFeature
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user


class TestChatFeature:
    def test_native_features_map_to_their_openwebui_capability(self) -> None:
        assert ChatFeature.WEB_SEARCH.openwebui_capability == "web_search"
        assert ChatFeature.CODE_INTERPRETER.openwebui_capability == "code_interpreter"
        assert ChatFeature.IMAGE_GENERATION.openwebui_capability == "image_generation"

    def test_toggle_filter_id_follows_the_function_id_scheme(self) -> None:
        """OpenWebUI derives a function's id from its file name with underscores turned into hyphens."""
        assert ChatFeature.IMAGE_GENERATION.openwebui_toggle_filter_id == "aihub-feature-image-generation"


class TestRequestedFeaturesOnTheEvent:
    def test_defaults_to_none_requested(self) -> None:
        event = UserMessageEvent(user=fake_user())

        assert event.requested_features == []

    def test_survives_serialization(self) -> None:
        event = UserMessageEvent(
            user=fake_user(),
            requested_features=[ChatFeature.WEB_SEARCH],
        )

        restored = BaseEvent.deserialize_event(event.model_dump_json(serialize_as_any=True))

        assert restored.requested_features == [ChatFeature.WEB_SEARCH]

    def test_lands_in_the_run_context(self) -> None:
        """The dispatcher copies the start event into the run context, where `RequestedFeatures` reads it."""
        event = UserMessageEvent(
            user=fake_user(),
            requested_features=[ChatFeature.CODE_INTERPRETER],
        )

        assert event.to_context_dict()["requested_features"] == ["code_interpreter"]
