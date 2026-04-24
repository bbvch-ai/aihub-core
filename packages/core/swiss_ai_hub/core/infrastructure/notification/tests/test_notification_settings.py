from swiss_ai_hub.core.infrastructure.notification.notification_settings import NotificationSettings


class TestNotificationSettingsUrlParsing:
    def test_unset_yields_empty_urls_and_disabled(self, monkeypatch) -> None:
        monkeypatch.delenv("NOTIFICATION_URLS", raising=False)
        settings = NotificationSettings()
        assert settings.URLS == []
        assert settings.enabled is False

    def test_empty_string_yields_empty_urls(self, monkeypatch) -> None:
        monkeypatch.setenv("NOTIFICATION_URLS", "")
        settings = NotificationSettings()
        assert settings.URLS == []
        assert settings.enabled is False

    def test_comma_separated_values_are_split(self, monkeypatch) -> None:
        monkeypatch.setenv("NOTIFICATION_URLS", "slack://a/b/c,mailto://u:p@smtp.example.com,msteams://d/e/f")
        settings = NotificationSettings()
        assert settings.URLS == ["slack://a/b/c", "mailto://u:p@smtp.example.com", "msteams://d/e/f"]
        assert settings.enabled is True

    def test_whitespace_and_empty_segments_are_stripped(self, monkeypatch) -> None:
        monkeypatch.setenv("NOTIFICATION_URLS", " slack://a/b/c ,, mailto://u:p@smtp.example.com , ")
        settings = NotificationSettings()
        assert settings.URLS == ["slack://a/b/c", "mailto://u:p@smtp.example.com"]
        assert settings.enabled is True

    def test_single_url_without_commas(self, monkeypatch) -> None:
        monkeypatch.setenv("NOTIFICATION_URLS", "slack://a/b/c/#ops")
        settings = NotificationSettings()
        assert settings.URLS == ["slack://a/b/c/#ops"]
        assert settings.enabled is True


class TestNotificationSettingsDefaults:
    def test_default_title_prefix(self, monkeypatch) -> None:
        monkeypatch.delenv("NOTIFICATION_TITLE_PREFIX", raising=False)
        assert NotificationSettings().TITLE_PREFIX == "Swiss AI Hub Pipeline"

    def test_default_min_interval_seconds(self, monkeypatch) -> None:
        monkeypatch.delenv("NOTIFICATION_MIN_INTERVAL_SECONDS", raising=False)
        assert NotificationSettings().MIN_INTERVAL_SECONDS == 30

    def test_default_dagster_ui_base_url_is_none(self, monkeypatch) -> None:
        monkeypatch.delenv("NOTIFICATION_DAGSTER_UI_BASE_URL", raising=False)
        assert NotificationSettings().DAGSTER_UI_BASE_URL is None

    def test_custom_title_prefix_and_interval(self, monkeypatch) -> None:
        monkeypatch.setenv("NOTIFICATION_TITLE_PREFIX", "Custom Prefix")
        monkeypatch.setenv("NOTIFICATION_MIN_INTERVAL_SECONDS", "120")
        settings = NotificationSettings()
        assert settings.TITLE_PREFIX == "Custom Prefix"
        assert settings.MIN_INTERVAL_SECONDS == 120
