"""Covers how a data lake folder is mapped to its namespace when two folders sanitise to the same name (#1927)."""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from mongoengine import DoesNotExist, NotUniqueError
from swiss_ai_hub.core.persistence.rag.datalake.entities import NamespaceEntity

from swiss_ai_hub.pipeline.util.bucket_utils import get_or_create_namespace_for_directory
from swiss_ai_hub.pipeline.util.namespace_collision_error import NamespaceCollisionError

_MODULE = "swiss_ai_hub.pipeline.util.bucket_utils"
BUCKET_ID = "6ab3763616f0bf3e684dd5b7"


@pytest.fixture
def namespaces() -> Iterator[MagicMock]:
    with (
        patch(f"{_MODULE}._ensure_connection"),
        patch(f"{_MODULE}._get_or_create_bucket", return_value=MagicMock(id=BUCKET_ID)),
        patch(f"{_MODULE}.NamespaceEntity") as namespace_cls,
    ):
        namespace_cls.sanitize_namespace_name.side_effect = NamespaceEntity.sanitize_namespace_name
        yield namespace_cls


def test_a_registered_folder_resolves_to_its_namespace(namespaces: MagicMock) -> None:
    namespaces.get_namespace_by_bucket_and_folder.return_value = MagicMock(namespace_name="hr_docs")

    assert get_or_create_namespace_for_directory("hrdocs", "hr docs") == "hr_docs"
    namespaces.create_namespace.assert_not_called()


def test_a_new_folder_is_registered(namespaces: MagicMock) -> None:
    namespaces.get_namespace_by_bucket_and_folder.side_effect = DoesNotExist
    namespaces.get_namespace_by_bucket_and_name.side_effect = DoesNotExist
    namespaces.create_namespace.return_value = MagicMock(namespace_name="policies")

    assert get_or_create_namespace_for_directory("hrdocs", "policies") == "policies"
    assert namespaces.create_namespace.call_args.kwargs["folder_name"] == "policies"


def test_a_folder_whose_name_another_folder_owns_is_refused_without_an_insert(namespaces: MagicMock) -> None:
    namespaces.get_namespace_by_bucket_and_folder.side_effect = DoesNotExist
    namespaces.get_namespace_by_bucket_and_name.return_value = MagicMock(folder_name="hr_docs")

    with pytest.raises(NamespaceCollisionError) as collision:
        get_or_create_namespace_for_directory("hrdocs", "hr docs")

    assert (collision.value.directory, collision.value.existing_folder) == ("hr docs", "hr_docs")
    assert collision.value.namespace_name == "hr_docs"
    assert "'hr docs'" in str(collision.value) and "'hr_docs'" in str(collision.value)
    namespaces.get_namespace_by_bucket_and_name.assert_called_once_with(
        bucket_id=BUCKET_ID, namespace_name="hr_docs", db_alias="default"
    )
    namespaces.create_namespace.assert_not_called()


def test_losing_a_creation_race_returns_the_namespace_the_other_run_created(namespaces: MagicMock) -> None:
    created_concurrently = MagicMock(namespace_name="policies")
    namespaces.get_namespace_by_bucket_and_folder.side_effect = [DoesNotExist, created_concurrently]
    namespaces.get_namespace_by_bucket_and_name.side_effect = DoesNotExist
    namespaces.create_namespace.side_effect = NotUniqueError

    assert get_or_create_namespace_for_directory("hrdocs", "policies") == "policies"


def test_losing_a_creation_race_to_a_colliding_folder_is_a_collision(namespaces: MagicMock) -> None:
    namespaces.get_namespace_by_bucket_and_folder.side_effect = DoesNotExist
    namespaces.get_namespace_by_bucket_and_name.side_effect = [DoesNotExist, MagicMock(folder_name="hr_docs")]
    namespaces.create_namespace.side_effect = NotUniqueError

    with pytest.raises(NamespaceCollisionError):
        get_or_create_namespace_for_directory("hrdocs", "hr docs")
