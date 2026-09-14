import pytest
from cryptography.fernet import Fernet, InvalidToken
from pydantic import SecretStr

from swiss_ai_hub.core.infrastructure.encryption.config_encryption_settings import ConfigEncryptionSettings
from swiss_ai_hub.core.secrets.secret_encryption_service import SecretEncryptionService


@pytest.fixture
def service() -> SecretEncryptionService:
    return SecretEncryptionService(Fernet.generate_key().decode())


class TestRoundTrip:
    def test_an_encrypted_value_decrypts_to_the_original(self, service: SecretEncryptionService):
        ciphertext = service.encrypt("s3cret")

        assert ciphertext != "s3cret"
        assert ciphertext.startswith("enc:v1:")
        assert service.decrypt(ciphertext) == "s3cret"

    def test_plaintext_passes_through_decryption_unchanged(self, service: SecretEncryptionService):
        assert service.decrypt("legacy-plaintext") == "legacy-plaintext"

    def test_ciphertext_is_not_encrypted_twice(self, service: SecretEncryptionService):
        ciphertext = service.encrypt("s3cret")

        assert service.encrypt(ciphertext) == ciphertext

    def test_none_and_empty_mean_no_secret(self, service: SecretEncryptionService):
        assert service.encrypt(None) is None
        assert service.encrypt("") == ""
        assert service.decrypt(None) is None

    def test_a_different_key_cannot_decrypt(self, service: SecretEncryptionService):
        ciphertext = service.encrypt("s3cret")
        other = SecretEncryptionService(Fernet.generate_key().decode())

        with pytest.raises(InvalidToken):
            other.decrypt(ciphertext)


class TestGuards:
    def test_the_mask_is_never_encrypted(self, service: SecretEncryptionService):
        with pytest.raises(ValueError, match="mask"):
            service.encrypt(SecretEncryptionService.MASK)

    def test_a_mask_carrying_a_handle_is_never_encrypted(self, service: SecretEncryptionService):
        masked = service.mask_paths({"api_key": service.encrypt("s3cret")}, {"api_key"})["api_key"]

        with pytest.raises(ValueError, match="mask"):
            service.encrypt(masked)

    def test_non_string_secrets_are_rejected(self, service: SecretEncryptionService):
        with pytest.raises(TypeError):
            service.encrypt(42)


class TestFromSettings:
    def test_a_missing_key_fails_closed_with_the_variable_name(self):
        settings = ConfigEncryptionSettings(ENCRYPTION_KEY=None)

        with pytest.raises(ValueError, match="AIHUB_CONFIG_ENCRYPTION_KEY"):
            SecretEncryptionService.from_settings(settings)

    def test_a_malformed_key_is_rejected(self):
        settings = ConfigEncryptionSettings(ENCRYPTION_KEY=SecretStr("not-a-key"))

        with pytest.raises(ValueError):
            SecretEncryptionService.from_settings(settings)

    def test_a_valid_key_builds_a_working_service(self):
        settings = ConfigEncryptionSettings(ENCRYPTION_KEY=SecretStr(Fernet.generate_key().decode()))

        service = SecretEncryptionService.from_settings(settings)

        assert service.decrypt(service.encrypt("s3cret")) == "s3cret"


class TestPaths:
    def test_only_the_named_paths_change_including_nested_and_repeated_ones(self, service: SecretEncryptionService):
        config = {
            "url": "https://mcp",
            "mcp": {"api_key": "k1", "timeout": 30},
            "servers": [{"api_key": "k2"}, {"api_key": ""}, {"name": "no-key"}],
        }

        encrypted = service.encrypt_paths(config, {"mcp.api_key", "servers.api_key"})

        assert encrypted["url"] == "https://mcp"
        assert encrypted["mcp"]["timeout"] == 30
        assert service.is_encrypted(encrypted["mcp"]["api_key"])
        assert service.is_encrypted(encrypted["servers"][0]["api_key"])
        assert encrypted["servers"][1]["api_key"] == ""
        assert encrypted["servers"][2] == {"name": "no-key"}
        assert config["mcp"]["api_key"] == "k1", "the input is not mutated"
        assert service.decrypt_paths(encrypted, {"mcp.api_key", "servers.api_key"}) == config

    def test_paths_absent_from_the_configuration_are_skipped(self, service: SecretEncryptionService):
        assert service.encrypt_paths({"a": 1}, {"missing.secret"}) == {"a": 1}


class TestMaskPaths:
    def test_set_secrets_are_masked_and_unset_ones_stay_visible_as_unset(self, service: SecretEncryptionService):
        config = {"mcp": {"api_key": "enc:v1:abc", "url": "u"}, "servers": [{"api_key": "enc:v1:x"}, {"api_key": ""}]}

        masked = service.mask_paths(config, {"mcp.api_key", "servers.api_key"})

        assert masked["mcp"]["url"] == "u"
        assert service.is_masked(masked["mcp"]["api_key"])
        assert service.is_masked(masked["servers"][0]["api_key"])
        assert masked["servers"][1]["api_key"] == ""

    def test_a_mask_reveals_neither_plaintext_nor_ciphertext(self, service: SecretEncryptionService):
        stored = service.encrypt_paths({"api_key": "sk-top"}, {"api_key"})

        masked = service.mask_paths(stored, {"api_key"})

        assert "sk-top" not in str(masked)
        assert "enc:v1:" not in str(masked)

    def test_distinct_secrets_get_distinct_handles(self, service: SecretEncryptionService):
        stored = service.encrypt_paths({"servers": [{"api_key": "a"}, {"api_key": "b"}]}, {"servers.api_key"})

        masked = service.mask_paths(stored, {"servers.api_key"})

        assert masked["servers"][0]["api_key"] != masked["servers"][1]["api_key"]

    def test_masking_is_idempotent(self, service: SecretEncryptionService):
        stored = service.encrypt_paths({"api_key": "sk-top"}, {"api_key"})

        once = service.mask_paths(stored, {"api_key"})

        assert service.mask_paths(once, {"api_key"}) == once

    def test_a_non_string_secret_is_rejected(self, service: SecretEncryptionService):
        with pytest.raises(TypeError):
            service.mask_paths({"api_key": 42}, {"api_key"})


class TestRestoreMaskedPaths:
    PATHS = {"servers.api_key"}

    def _stored(self, service: SecretEncryptionService, *secrets: str) -> dict:
        return service.encrypt_paths({"servers": [{"api_key": s} for s in secrets]}, self.PATHS)

    def _secrets(self, service: SecretEncryptionService, restored: dict) -> list:
        decrypted = service.decrypt_paths(restored, self.PATHS)
        return [row.get("api_key") for row in decrypted["servers"]]

    def test_a_resubmitted_mask_keeps_the_stored_secret_and_a_new_value_replaces_it(
        self, service: SecretEncryptionService
    ):
        stored = self._stored(service, "s0", "s1")
        masked = service.mask_paths(stored, self.PATHS)
        submitted = {"servers": [{"api_key": "fresh"}, masked["servers"][1]]}

        restored = service.restore_masked_paths(submitted, stored, self.PATHS)

        assert self._secrets(service, restored) == ["fresh", "s1"]

    def test_reordered_rows_keep_their_own_secrets(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha", "beta")
        masked = service.mask_paths(stored, self.PATHS)
        submitted = {"servers": [masked["servers"][1], masked["servers"][0]]}

        restored = service.restore_masked_paths(submitted, stored, self.PATHS)

        assert self._secrets(service, restored) == ["beta", "alpha"]

    def test_deleting_a_leading_row_leaves_the_survivor_with_its_own_secret(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha", "beta")
        masked = service.mask_paths(stored, self.PATHS)
        submitted = {"servers": [masked["servers"][1]]}

        restored = service.restore_masked_paths(submitted, stored, self.PATHS)

        assert self._secrets(service, restored) == ["beta"]

    def test_inserting_a_row_neither_errors_nor_shifts_the_others(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha", "beta")
        masked = service.mask_paths(stored, self.PATHS)
        submitted = {"servers": [{"api_key": "new"}, masked["servers"][0], masked["servers"][1]]}

        restored = service.restore_masked_paths(submitted, stored, self.PATHS)

        assert self._secrets(service, restored) == ["new", "alpha", "beta"]

    def test_a_row_omitting_the_secret_does_not_shift_the_others(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha", "beta")
        masked = service.mask_paths(stored, self.PATHS)
        submitted = {"servers": [{"name": "no-key"}, masked["servers"][1]]}

        restored = service.restore_masked_paths(submitted, stored, self.PATHS)

        assert self._secrets(service, restored) == [None, "beta"]

    def test_rows_sharing_a_secret_both_restore_it_after_a_reorder(self, service: SecretEncryptionService):
        stored = {"servers": [{"api_key": "enc:v1:same"}, {"api_key": "enc:v1:same"}]}
        masked = service.mask_paths(stored, self.PATHS)
        submitted = {"servers": [masked["servers"][1], masked["servers"][0]]}

        restored = service.restore_masked_paths(submitted, stored, self.PATHS)

        assert [row["api_key"] for row in restored["servers"]] == ["enc:v1:same", "enc:v1:same"]

    def test_a_legacy_plaintext_secret_survives_the_round_trip_and_is_encrypted_on_the_way_out(
        self, service: SecretEncryptionService
    ):
        stored = {"servers": [{"api_key": "legacy-plaintext"}]}
        masked = service.mask_paths(stored, self.PATHS)

        restored = service.restore_masked_paths({"servers": [masked["servers"][0]]}, stored, self.PATHS)
        sealed = service.encrypt_paths(restored, self.PATHS)

        assert service.is_encrypted(sealed["servers"][0]["api_key"])
        assert self._secrets(service, sealed) == ["legacy-plaintext"]

    def test_clearing_a_secret_is_an_empty_string_not_a_mask(self, service: SecretEncryptionService):
        stored = self._stored(service, "old")

        restored = service.restore_masked_paths({"servers": [{"api_key": ""}]}, stored, self.PATHS)

        assert restored["servers"][0]["api_key"] == ""

    def test_a_bare_mask_without_a_handle_is_a_client_error(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha")
        submitted = {"servers": [{"api_key": SecretEncryptionService.MASK}]}

        with pytest.raises(ValueError, match="servers.api_key"):
            service.restore_masked_paths(submitted, stored, self.PATHS)

    def test_an_unknown_handle_is_a_client_error(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha")
        submitted = {"servers": [{"api_key": f"{SecretEncryptionService.MASK}:deadbeefdeadbeef"}]}

        with pytest.raises(ValueError, match="servers.api_key"):
            service.restore_masked_paths(submitted, stored, self.PATHS)

    def test_a_handle_minted_under_another_key_does_not_resolve(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha")
        other = SecretEncryptionService(Fernet.generate_key().decode())
        submitted = other.mask_paths(stored, self.PATHS)

        with pytest.raises(ValueError, match="servers.api_key"):
            service.restore_masked_paths(submitted, stored, self.PATHS)

    def test_a_handle_does_not_resolve_against_a_different_path(self, service: SecretEncryptionService):
        stored = service.encrypt_paths({"mcp": {"api_key": "m"}, "servers": [{"api_key": "s"}]}, {"mcp.api_key"})
        masked = service.mask_paths(stored, {"mcp.api_key"})
        submitted = {"mcp": stored["mcp"], "servers": [{"api_key": masked["mcp"]["api_key"]}]}

        with pytest.raises(ValueError, match="servers.api_key"):
            service.restore_masked_paths(submitted, stored, self.PATHS)

    def test_a_non_string_at_a_secret_path_does_not_crash_restore(self, service: SecretEncryptionService):
        stored = self._stored(service, "alpha")

        restored = service.restore_masked_paths({"servers": [{"api_key": {"a": 1}}]}, stored, self.PATHS)

        assert restored["servers"][0]["api_key"] == {"a": 1}
