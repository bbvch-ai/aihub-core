"""The rule for names the platform is asked to create is a pure predicate, so it lives apart from the
entity tests that need a Mongo connection to save a row."""

import pytest
from mongoengine import ValidationError

from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity


class TestNewDatabaseNameValidation:
    @pytest.mark.parametrize(
        "name",
        ["MyDb", "myDb", "1db", "ab", "a" * 64, "my-db", "my_db", "my db", "my.db", "", "mydb\n", "a" * 63 + "\n"],
    )
    def test_rejects_a_name_no_store_would_accept(self, name):
        with pytest.raises(ValidationError):
            BucketEntity.validate_new_database_name(name)

    @pytest.mark.parametrize("name", ["mydb", "abc", "db001", "a" * 63])
    def test_accepts_a_lowercase_alphanumeric_name(self, name):
        BucketEntity.validate_new_database_name(name)
