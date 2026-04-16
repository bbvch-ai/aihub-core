from swiss_ai_hub.backup.models import BackupEntry

import pytest

def test_backup_entry_stores_prefix_and_count() -> None:
    entry = BackupEntry(prefix="2026-02-19_02-00-00", file_count=5)
    assert entry.prefix == "2026-02-19_02-00-00"
    assert entry.file_count == 5


def test_backup_entry_empty() -> None:
    entry = BackupEntry(prefix="", file_count=0)
    assert entry.prefix == ""
    assert entry.file_count == 0
