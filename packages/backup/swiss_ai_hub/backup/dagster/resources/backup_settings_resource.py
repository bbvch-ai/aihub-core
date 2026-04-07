from dagster import ConfigurableResource, InitResourceContext

from swiss_ai_hub.backup.settings import BackupSettings


class BackupSettingsResource(ConfigurableResource[BackupSettings]):
    def create_resource(self, context: InitResourceContext) -> BackupSettings:
        # Required SecretStr fields are loaded from env vars by pydantic-settings at runtime
        return BackupSettings()  # type: ignore[call-arg]
