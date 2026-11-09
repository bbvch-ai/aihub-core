import pytest
from pydantic import ValidationError
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.group import Group
from swiss_ai_hub.core.form.elements.secret_file_input import SecretFileInput
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.infrastructure.rclone import RcloneBackendType

from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig


def _offered(elements: dict) -> list[str]:
    return [option["value"] for option in elements["backend_type"].options]


class TestAnnouncedForm:
    def test_one_group_per_backend_shown_only_for_the_selected_backend(self, monkeypatch):
        monkeypatch.setenv("RCLONE_LOCAL_SOURCE_ROOT", "/data")
        elements = {element.name: element for element in RcloneSyncConfig.as_form().to_formkit_form()}

        assert isinstance(elements["backend_type"], Select)
        assert _offered(elements) == ["onedrive", "drive", "s3", "local"]
        groups = {name: element for name, element in elements.items() if isinstance(element, Group)}
        assert set(groups) == {"onedrive", "drive", "s3", "azureblob", "sftp"}, "local has no options and no group"
        for name, group in groups.items():
            assert group.condition_if == f"$get(rclone_backend_type).value === '{name}'"
            assert group.nullable is False

    def test_the_local_backend_is_not_offered_unless_the_deployment_names_a_root(self, monkeypatch):
        monkeypatch.delenv("RCLONE_LOCAL_SOURCE_ROOT", raising=False)
        elements = {element.name: element for element in RcloneSyncConfig.as_form().to_formkit_form()}

        assert _offered(elements) == ["onedrive", "drive", "s3"]

    def test_backends_not_yet_verified_end_to_end_are_not_offered_but_still_run(self, monkeypatch):
        monkeypatch.setenv("RCLONE_LOCAL_SOURCE_ROOT", "/data")
        elements = {element.name: element for element in RcloneSyncConfig.as_form().to_formkit_form()}
        offered = _offered(elements)

        for untested in ("azureblob", "sftp"):
            assert untested not in offered
        config = RcloneSyncConfig.model_validate(
            {"backend_type": "sftp", "sftp": {"host": "files.acme", "user": "u", "password": "p"}}
        )
        assert config.to_rclone_source_config("r").backend_type is RcloneBackendType.SFTP

    def test_backends_are_offered_by_name_while_their_value_drives_the_option_groups(self):
        """The stored value and every group's ``condition_if`` keep comparing the token; only the label changed."""
        elements = {element.name: element for element in RcloneSyncConfig.as_form().to_formkit_form()}
        backend_type = elements["backend_type"]

        assert (backend_type.option_label, backend_type.option_value) == ("label", "value")
        onedrive = next(option for option in backend_type.options if option["value"] == "onedrive")
        assert onedrive["label"].en == "OneDrive / SharePoint"

    def test_the_drive_service_account_is_picked_as_a_json_key_file(self):
        elements = {element.name: element for element in RcloneSyncConfig.as_form().to_formkit_form()}
        drive_fields = {child.name: child for child in elements["drive"].children}

        key_file = drive_fields["service_account_credentials"]
        assert isinstance(key_file, SecretFileInput)
        assert key_file.accept == ".json"
        assert key_file.condition_if == "$get(rclone_backend_type).value === 'drive'"

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

    def test_onedrive_answers_rclones_setup_with_the_drive_so_rclone_checks_it_up_front(self):
        """Without these answers rclone stops at "Type of connection" and the remote is never created."""
        config = RcloneSyncConfig.model_validate(
            {"backend_type": "onedrive", "onedrive": {"drive_id": "b!abc", "token": '{"access_token":"x"}'}}
        )

        options = config.to_rclone_source_config("r").options

        assert {key: value for key, value in options.items() if key.startswith("config_")} == {
            "config_type": "driveid",
            "config_driveid_fixed": "b!abc",
            "config_driveid": "b!abc",
            "config_drive_ok": "true",
        }
        assert "client_credentials" not in options, "a pasted token is a delegated sign-in, not client credentials"

    def test_only_onedrive_gets_setup_answers(self):
        config = RcloneSyncConfig.model_validate(
            {"backend_type": "drive", "drive": {"service_account_credentials": '{"type":"service_account"}'}}
        )

        assert not any(key.startswith("config_") for key in config.to_rclone_source_config("r").options)

    def test_a_backend_missing_its_required_options_is_rejected_before_reaching_rclone(self):
        config = RcloneSyncConfig.model_validate({"backend_type": "s3", "s3": {"access_key_id": "only-the-id"}})

        with pytest.raises(ValueError, match="access_key_id\\+secret_access_key"):
            config.to_rclone_source_config("r")

    def test_the_remote_spec_keeps_local_paths_absolute_and_strips_cloud_paths(self, monkeypatch):
        monkeypatch.setenv("RCLONE_LOCAL_SOURCE_ROOT", "/data")
        cloud = RcloneSyncConfig.model_validate({"backend_type": "s3", "root_path": "/bucket/docs/"})
        local = RcloneSyncConfig.model_validate({"backend_type": "local", "root_path": "/data/shared"})

        assert cloud.remote_fs("r") == "r:bucket/docs"
        assert local.remote_fs("r") == "r:/data/shared"
        assert local.to_rclone_source_config("r").options == {}


class TestLocalBackendConfinement:
    def test_a_local_source_is_refused_per_run_where_the_deployment_allows_no_directory(self, monkeypatch):
        monkeypatch.delenv("RCLONE_LOCAL_SOURCE_ROOT", raising=False)
        config = RcloneSyncConfig.model_validate({"backend_type": "local", "root_path": "/etc"})

        with pytest.raises(ValueError, match="RCLONE_LOCAL_SOURCE_ROOT"):
            config.remote_fs("r")

    @pytest.mark.parametrize("escape", ["/etc", "/data/../etc", "/data2", "/"])
    def test_a_root_outside_the_allowed_directory_is_refused(self, monkeypatch, escape):
        monkeypatch.setenv("RCLONE_LOCAL_SOURCE_ROOT", "/data/")
        config = RcloneSyncConfig.model_validate({"backend_type": "local", "root_path": escape})

        with pytest.raises(ValueError, match="may only read below '/data'"):
            config.remote_fs("r")

    def test_an_empty_root_path_means_the_allowed_directory_itself(self, monkeypatch):
        monkeypatch.setenv("RCLONE_LOCAL_SOURCE_ROOT", "/data")
        config = RcloneSyncConfig.model_validate({"backend_type": "local"})

        assert config.remote_fs("r") == "r:/data"


class TestMultiLineSecrets:
    def test_a_pretty_printed_service_account_file_is_sent_to_rclone_on_one_line(self):
        pretty = (
            '{\n  "type": "service_account",\n'
            '  "private_key": "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n"\n}\n'
        )
        config = RcloneSyncConfig.model_validate(
            {"backend_type": "drive", "drive": {"service_account_credentials": pretty}}
        )

        sent = config.to_rclone_source_config("r").options["service_account_credentials"]

        assert "\n" not in sent
        expected = '{"type":"service_account","private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n'
        expected += '-----END PRIVATE KEY-----\\n"}'
        assert sent == expected

    def test_credentials_that_are_not_json_are_rejected_with_the_field_named(self):
        with pytest.raises(ValueError, match="Google Drive credentials"):
            RcloneSyncConfig.model_validate({"backend_type": "drive", "drive": {"token": "not json"}})

    @pytest.mark.parametrize("token", ["SECRET-not-json", '["SECRET"]', '"SECRET"'])
    def test_a_onedrive_token_that_is_not_a_json_object_is_rejected_without_quoting_it(self, token: str):
        with pytest.raises(ValidationError) as rejected:
            RcloneSyncConfig.model_validate(
                {"backend_type": "onedrive", "onedrive": {"drive_id": "b!a", "token": token}}
            )

        assert "onedrive.token" in str(rejected.value)
        assert "OneDrive token must be the JSON object" in str(rejected.value)
        assert "SECRET" not in str(rejected.value)

    def test_a_onedrive_token_object_is_sent_to_rclone_as_pasted(self):
        pasted = '{"access_token":"x","refresh_token":"y","expiry":"2026-11-08T19:20:00+07:00"}'
        config = RcloneSyncConfig.model_validate(
            {"backend_type": "onedrive", "onedrive": {"drive_id": "b!a", "token": pasted}}
        )

        assert config.to_rclone_source_config("r").options["token"] == pasted

    def test_a_pasted_pem_key_reaches_rclone_with_escaped_line_breaks(self):
        pasted = "-----BEGIN OPENSSH PRIVATE KEY-----\r\nabc\r\ndef\r\n-----END OPENSSH PRIVATE KEY-----\r\n"
        config = RcloneSyncConfig.model_validate(
            {"backend_type": "sftp", "sftp": {"host": "h", "user": "u", "key_pem": pasted}}
        )

        sent = config.to_rclone_source_config("r").options["key_pem"]

        assert sent == "-----BEGIN OPENSSH PRIVATE KEY-----\\nabc\\ndef\\n-----END OPENSSH PRIVATE KEY-----"

    def test_the_announced_form_still_builds_with_the_validators_in_place(self):
        assert RcloneSyncConfig.as_form() is not None


class TestValidationErrors:
    def test_a_rejected_secret_is_not_quoted_in_the_error(self):
        """The pipeline validates after decrypting, and the error lands in the run log and the failure notification."""
        with pytest.raises(ValidationError) as rejected:
            RcloneSyncConfig.model_validate(
                {"backend_type": "s3", "s3": {"access_key_id": "id", "secret_access_key": ["AKIA-SECRET-VALUE"]}}
            )

        assert "s3.secret_access_key" in str(rejected.value)
        assert "AKIA-SECRET-VALUE" not in str(rejected.value)


def _onedrive_token_mode(**onedrive: str) -> RcloneSyncConfig:
    return RcloneSyncConfig.model_validate(
        {"backend_type": "onedrive", "onedrive": {"drive_id": "b!abc", "token": '{"access_token":"x"}', **onedrive}}
    )


class TestOneDriveTokenUrl:
    """rclone's OneDrive setup refreshes an expired pasted token with a client that has no token URL of its own;
    without ``token_url`` the remote fails with ``Post "": unsupported protocol scheme`` about an hour after the
    token was pasted."""

    def test_a_token_from_rclones_own_app_is_refreshed_at_the_common_endpoint(self):
        options = _onedrive_token_mode().to_rclone_source_config("r").options

        assert options["token_url"] == "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    def test_a_tenant_gets_its_own_endpoint(self):
        tenant = "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0"

        options = _onedrive_token_mode(tenant=tenant).to_rclone_source_config("r").options

        assert options["token_url"] == f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    @pytest.mark.parametrize(
        ("region", "host"),
        [
            ("global", "login.microsoftonline.com"),
            ("us", "login.microsoftonline.us"),
            ("de", "login.microsoftonline.de"),
            ("cn", "login.chinacloudapi.cn"),
        ],
    )
    def test_the_region_selects_rclones_login_host(self, region: str, host: str):
        options = _onedrive_token_mode(region=region).to_rclone_source_config("r").options

        assert options["token_url"] == f"https://{host}/common/oauth2/v2.0/token"

    def test_a_tenant_cannot_move_the_endpoint_off_the_login_host(self):
        options = _onedrive_token_mode(tenant="evil.example/x@y?z#").to_rclone_source_config("r").options

        assert options["token_url"] == (
            "https://login.microsoftonline.com/evil.example%2Fx%40y%3Fz%23/oauth2/v2.0/token"
        )

    def test_an_unknown_region_is_refused(self):
        config = _onedrive_token_mode(region="mars")

        with pytest.raises(ValueError, match="Unknown OneDrive region 'mars'"):
            config.to_rclone_source_config("r")

    def test_client_credentials_are_unchanged_and_get_no_token_url(self):
        config = RcloneSyncConfig.model_validate(
            {
                "backend_type": "onedrive",
                "onedrive": {"client_id": "c", "client_secret": "s", "tenant": "t", "drive_id": "d"},
            }
        )

        options = config.to_rclone_source_config("r").options

        assert "token_url" not in options
        assert options["client_credentials"] == "true"

    def test_the_token_url_is_never_part_of_what_is_stored(self):
        config = _onedrive_token_mode()

        assert "token_url" not in config.model_dump()["onedrive"]


class TestRefreshableTokenPath:
    @pytest.mark.parametrize(
        ("submission", "path"),
        [
            ({"backend_type": "onedrive", "onedrive": {"drive_id": "d", "token": "{}"}}, "onedrive.token"),
            ({"backend_type": "drive", "drive": {"token": "{}"}}, "drive.token"),
            (
                {
                    "backend_type": "onedrive",
                    "onedrive": {"client_id": "c", "client_secret": "s", "tenant": "t", "drive_id": "d"},
                },
                None,
            ),
            ({"backend_type": "drive", "drive": {"service_account_credentials": "{}"}}, None),
            ({"backend_type": "sftp", "sftp": {"host": "h", "user": "u", "password": "p"}}, None),
            ({"backend_type": "s3", "s3": {"access_key_id": "a", "secret_access_key": "s"}}, None),
        ],
    )
    def test_only_a_pasted_oauth_token_is_refreshable(self, submission: dict, path: str | None):
        assert RcloneSyncConfig.model_validate(submission).refreshable_token_path() == path

    def test_a_token_left_in_a_hidden_group_does_not_count(self):
        config = RcloneSyncConfig.model_validate(
            {
                "backend_type": "s3",
                "s3": {"access_key_id": "a", "secret_access_key": "s"},
                "onedrive": {"token": "{}"},
            }
        )

        assert config.refreshable_token_path() is None
