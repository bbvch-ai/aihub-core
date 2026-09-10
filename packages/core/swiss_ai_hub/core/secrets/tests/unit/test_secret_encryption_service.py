import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from swiss_ai_hub.core.infrastructure.encryption.config_encryption_settings import ConfigEncryptionSettings
from swiss_ai_hub.core.secrets.secret_encryption_service import SecretEncryptionService
from swiss_ai_hub.core.secrets.secret_masker import SecretMasker


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
        other = SecretEncryptionService(Fernet.generate_key().decode())

        with pytest.raises(Exception):
            other.decrypt(service.encrypt("s3cret"))


class TestGuards:
    def test_the_mask_is_never_encrypted(self, service: SecretEncryptionService):
        with pytest.raises(ValueError, match="mask"):
            service.encrypt(SecretMasker.MASK)

    def test_non_string_secrets_are_rejected(self, service: SecretEncryptionService):
        with pytest.raises(TypeError):
            service.encrypt(42)


class TestFromSettings:
    def test_a_missing_key_fails_closed_with_the_variable_name(self):
        with pytest.raises(ValueError, match="AIHUB_CONFIG_ENCRYPTION_KEY"):
            SecretEncryptionService.from_settings(ConfigEncryptionSettings(ENCRYPTION_KEY=None))

    def test_a_malformed_key_is_rejected(self):
        with pytest.raises(ValueError):
            SecretEncryptionService.from_settings(ConfigEncryptionSettings(ENCRYPTION_KEY=SecretStr("not-a-key")))

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
