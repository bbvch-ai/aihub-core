import pytest
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.group import Group
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.infrastructure.rclone import RcloneBackendType

from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig


class TestAnnouncedForm:
    def test_one_group_per_backend_shown_only_for_the_selected_backend(self):
        elements = {element.name: element for element in RcloneSyncConfig.as_form().to_formkit_form()}

        assert isinstance(elements["backend_type"], Select)
        assert elements["backend_type"].options == [backend.value for backend in RcloneBackendType]
        groups = {name: element for name, element in elements.items() if isinstance(element, Group)}
        assert set(groups) == {"onedrive", "drive", "s3", "azureblob", "sftp"}, "local has no options and no group"
        for name, group in groups.items():
            assert group.condition_if == f"$get(rclone_backend_type).value === '{name}'"
            assert group.nullable is False

    def test_every_credential_is_a_secret_path_derived_from_the_form(self):
        assert RcloneSyncConfig.secret_field_paths() == {
            "onedrive.client_secret",
            "onedrive.token",
            "drive.client_secret",
            "drive.token",
            "drive.service_account_credentials",
            "s3.secret_access_key",
            "azureblob.key",
            "azureblob.sas_url",
            "sftp.password",
            "sftp.key_pem",
        }

    def test_the_schema_accepts_a_submission_carrying_only_the_selected_backend(self):
        specs = ConfigSpecs.from_form(RcloneSyncConfig.as_form(), "RcloneSyncConfig")

        assert {"backend_type", "root_path", "include_patterns", "exclude_patterns", "sftp"} <= set(
            specs.config_schema["properties"]
        )
        config = RcloneSyncConfig.model_validate(
            {
                "backend_type": "sftp",
                "root_path": "/srv/docs",
                "sftp": {"host": "files.acme", "user": "u", "password": "p"},
            }
        )
        assert config.onedrive.client_id == ""


class TestToRcloneSourceConfig:
    def test_the_selected_backend_is_emitted_without_empty_options_and_with_rclone_spelling(self):
        config = RcloneSyncConfig.model_validate(
            {"backend_type": "sftp", "sftp": {"host": "files.acme", "user": "u", "password": "p", "port": 2222}}
        )

        remote = config.to_rclone_source_config("rclone_hrdocs")

        assert remote.name == "rclone_hrdocs"
        assert remote.backend_type is RcloneBackendType.SFTP
        assert remote.options == {"host": "files.acme", "user": "u", "pass": "p", "port": 2222}

    def test_onedrive_client_credentials_are_flagged_for_rclone_when_no_token_is_given(self):
        config = RcloneSyncConfig.model_validate(
            {
                "backend_type": "onedrive",
                "onedrive": {
                    "client_id": "c",
                    "client_secret": "s",
                    "tenant": "t",
                    "drive_id": "d",
                    "drive_type": "documentLibrary",
                },
            }
        )

        options = config.to_rclone_source_config("r").options

        assert options["client_credentials"] == "true"
        assert options["drive_type"] == "documentLibrary"

    def test_a_backend_missing_its_required_options_is_rejected_before_reaching_rclone(self):
        config = RcloneSyncConfig.model_validate({"backend_type": "s3", "s3": {"access_key_id": "only-the-id"}})

        with pytest.raises(ValueError, match="access_key_id\\+secret_access_key"):
            config.to_rclone_source_config("r")

    def test_the_remote_spec_keeps_local_paths_absolute_and_strips_cloud_paths(self):
        cloud = RcloneSyncConfig.model_validate({"backend_type": "s3", "root_path": "/bucket/docs/"})
        local = RcloneSyncConfig.model_validate({"backend_type": "local", "root_path": "/data/shared"})

        assert cloud.remote_fs("r") == "r:bucket/docs"
        assert local.remote_fs("r") == "r:/data/shared"
        assert local.to_rclone_source_config("r").options == {}
