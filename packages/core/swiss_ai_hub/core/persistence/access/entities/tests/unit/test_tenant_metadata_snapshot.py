from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from mongoengine import signals
from pymongo.errors import DuplicateKeyError

from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity


@pytest.fixture
def persisted_metadata() -> dict[str, Any]:
    return {
        "_id": "existing-tenant",
        "name": "Existing Tenant",
        "description": "Existing metadata",
        "access_rules": ["aihub.admin.>"],
        "chat_disclaimer": {"en": "Verify answers."},
        "lcdm_tenant_id": 5,
        "openwebui_mods_json": '{"version":3,"mods":[]}',
        "created_at": datetime(2024, 1, 2, tzinfo=UTC),
        "updated_at": datetime(2025, 3, 4, tzinfo=UTC),
        "unmodeled_settings": {"nested": ["preserve"]},
    }


def test_snapshot_preserves_raw_fields_without_sharing_mutable_values(
    monkeypatch: pytest.MonkeyPatch, persisted_metadata: dict[str, Any]
) -> None:
    collection = MagicMock()
    collection.find_one.return_value = persisted_metadata
    monkeypatch.setattr(TenantMetadataEntity, "_get_collection", lambda: collection)
    original = deepcopy(persisted_metadata)

    snapshot = TenantMetadataEntity.snapshot_tenant_metadata("existing-tenant")
    persisted_metadata["openwebui_mods_json"] = '{"version":4,"mods":[]}'
    persisted_metadata["access_rules"].clear()
    persisted_metadata["chat_disclaimer"]["en"] = "Changed later"
    persisted_metadata["unmodeled_settings"]["nested"].clear()

    assert snapshot == original
    collection.find_one.assert_called_once_with({"_id": "existing-tenant"})


def test_restore_preserves_raw_document_and_emits_save_notification_after_insert(
    monkeypatch: pytest.MonkeyPatch, persisted_metadata: dict[str, Any]
) -> None:
    collection = MagicMock()
    monkeypatch.setattr(TenantMetadataEntity, "_get_collection", lambda: collection)
    notified = MagicMock(side_effect=lambda *_args, **_kwargs: collection.insert_one.assert_called_once())
    with signals.post_save.connected_to(notified, sender=TenantMetadataEntity):
        restored = TenantMetadataEntity.restore_tenant_metadata(persisted_metadata)

    collection.insert_one.assert_called_once_with(persisted_metadata)
    notified.assert_called_once_with(TenantMetadataEntity, document=restored, created=True)
    assert restored.id == persisted_metadata["_id"]
    assert restored.created_at == persisted_metadata["created_at"]
    assert restored.updated_at == persisted_metadata["updated_at"]
    assert restored.openwebui_mods_json == persisted_metadata["openwebui_mods_json"]
    assert restored.lcdm_tenant_id == persisted_metadata["lcdm_tenant_id"]
    assert restored.chat_disclaimer.en == "Verify answers."
    assert restored._data["unmodeled_settings"] == persisted_metadata["unmodeled_settings"]


def test_restore_does_not_overwrite_a_concurrent_recreation_or_notify_after_failure(
    monkeypatch: pytest.MonkeyPatch, persisted_metadata: dict[str, Any]
) -> None:
    collection = MagicMock()
    collection.insert_one.side_effect = DuplicateKeyError("Tenant was recreated")
    monkeypatch.setattr(TenantMetadataEntity, "_get_collection", lambda: collection)
    notified = MagicMock()
    with signals.post_save.connected_to(notified, sender=TenantMetadataEntity):
        with pytest.raises(DuplicateKeyError):
            TenantMetadataEntity.restore_tenant_metadata(persisted_metadata)

    notified.assert_not_called()
    collection.replace_one.assert_not_called()
    collection.update_one.assert_not_called()
