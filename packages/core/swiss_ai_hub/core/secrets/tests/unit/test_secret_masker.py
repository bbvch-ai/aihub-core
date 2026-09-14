import pytest

from swiss_ai_hub.core.secrets.secret_masker import SecretMasker


class TestMaskPaths:
    def test_set_secrets_are_masked_and_unset_ones_stay_visible_as_unset(self):
        config = {"mcp": {"api_key": "enc:v1:abc", "url": "u"}, "servers": [{"api_key": "enc:v1:x"}, {"api_key": ""}]}

        masked = SecretMasker.mask_paths(config, {"mcp.api_key", "servers.api_key"})

        assert masked["mcp"] == {"api_key": SecretMasker.MASK, "url": "u"}
        assert masked["servers"] == [{"api_key": SecretMasker.MASK}, {"api_key": ""}]


class TestRestoreMaskedPaths:
    def test_a_resubmitted_mask_keeps_the_stored_secret_and_a_new_value_replaces_it(self):
        stored = {"mcp": {"api_key": "enc:v1:old"}, "servers": [{"api_key": "enc:v1:s0"}, {"api_key": "enc:v1:s1"}]}
        submitted = {
            "mcp": {"api_key": SecretMasker.MASK, "url": "changed"},
            "servers": [{"api_key": "fresh"}, {"api_key": SecretMasker.MASK}],
        }

        restored = SecretMasker.restore_masked_paths(submitted, stored, {"mcp.api_key", "servers.api_key"})

        assert restored["mcp"] == {"api_key": "enc:v1:old", "url": "changed"}
        assert restored["servers"] == [{"api_key": "fresh"}, {"api_key": "enc:v1:s1"}]

    def test_a_mask_without_a_stored_secret_is_a_client_error(self):
        with pytest.raises(ValueError, match="mcp.api_key"):
            SecretMasker.restore_masked_paths({"mcp": {"api_key": SecretMasker.MASK}}, {"mcp": {}}, {"mcp.api_key"})

    def test_clearing_a_secret_is_an_empty_string_not_a_mask(self):
        restored = SecretMasker.restore_masked_paths(
            {"mcp": {"api_key": ""}}, {"mcp": {"api_key": "enc:v1:old"}}, {"mcp.api_key"}
        )

        assert restored["mcp"]["api_key"] == ""
