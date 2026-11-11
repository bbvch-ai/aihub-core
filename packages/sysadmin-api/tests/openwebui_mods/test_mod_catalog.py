import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModBundles
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModRevisionEntity

from tests.openwebui_mods.test_mod_upload import archive, auth, client, host, publication, storage  # noqa: F401


def test_catalog_contains_current_builtins_without_seeding(client: TestClient, storage: MagicMock) -> None:
    response = client.get('/api/v1/admin/openwebui-mods/catalog')
    assert response.status_code == 200
    packages = OpenWebuiModBundles.packages()
    assert {item['manifest']['id']: item['source_revision'] for item in response.json()} == {
        mod_id: package.revision for mod_id, package in packages.items()
    }
    assert all(item['builtin'] for item in response.json())
    assert OpenWebuiModRevisionEntity.objects.count() == 0
    assert storage.mock_calls == []


def test_catalog_paginates_mods_independently_of_revision_history(client: TestClient) -> None:
    now = datetime.now(UTC)
    for index in range(105):
        mod_id = 'zz-many-versions' if index else 'aa-old-mod'
        manifest = {'format': 1, 'id': mod_id, 'name': mod_id, 'version': str(index), 'frontend': 'main.js'}
        OpenWebuiModRevisionEntity(
            revision=f'{index:064x}', mod_id=mod_id, manifest_json=json.dumps(manifest), archive_bytes=1,
            uploaded_at=now + timedelta(seconds=index), uploaded_by='fixture',
        ).save()
    entries = []
    for offset in range(5):
        entries.extend(client.get('/api/v1/admin/openwebui-mods/catalog', params={'offset': offset, 'limit': 1}).json())
    expected = sorted(['aa-old-mod', 'zz-many-versions', *OpenWebuiModBundles.packages()])
    assert [entry['manifest']['id'] for entry in entries] == expected
    assert entries[-1]['manifest']['version'] == '104'
    assert entries[-1]['builtin'] is False
