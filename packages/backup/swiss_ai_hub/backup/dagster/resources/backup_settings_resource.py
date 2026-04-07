from dagster import ConfigurableResource, InitResourceContext

from swiss_ai_hub.backup.settings import BackupSettings


class BackupSettingsResource(ConfigurableResource[BackupSettings]):
    def create_resource(self, context: InitResourceContext) -> BackupSettings:
        # SecretStr fields have no defaults — pydantic-settings loads them from env at runtime
        return BackupSettings()  # type: ignore[call-arg]
