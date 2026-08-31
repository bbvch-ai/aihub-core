from unittest.mock import patch

import pytest
from mongoengine.connection import ConnectionFailure

from swiss_ai_hub.core.infrastructure.mongo.mongo_connection_registry import MongoConnectionRegistry

_MODULE = "swiss_ai_hub.core.infrastructure.mongo.mongo_connection_registry"


class TestEnsureAlias:
    def test_registers_an_alias_that_does_not_exist_yet(self):
        """Knowledge databases are created at runtime, so their aliases cannot be registered at startup."""
        with (
            patch(f"{_MODULE}.mongoengine.connection.get_connection", side_effect=ConnectionFailure("no alias")),
            patch(f"{_MODULE}.register_connection") as register,
            patch(f"{_MODULE}.MongoSettings"),
        ):
            MongoConnectionRegistry.ensure_alias("researchdocs")

        assert register.call_args.kwargs["alias"] == "researchdocs"
        assert register.call_args.kwargs["name"] == "researchdocs"
        assert register.call_args.kwargs["uuidRepresentation"] == "standard"

    def test_registering_an_existing_alias_is_a_no_op(self):
        with (
            patch(f"{_MODULE}.mongoengine.connection.get_connection"),
            patch(f"{_MODULE}.register_connection") as register,
        ):
            MongoConnectionRegistry.ensure_alias("researchdocs")

        register.assert_not_called()

    def test_an_alias_may_differ_from_the_database_name(self):
        with (
            patch(f"{_MODULE}.mongoengine.connection.get_connection", side_effect=ConnectionFailure("no alias")),
            patch(f"{_MODULE}.register_connection") as register,
            patch(f"{_MODULE}.MongoSettings"),
        ):
            MongoConnectionRegistry.ensure_alias("aihub", alias="default")

        assert register.call_args.kwargs["alias"] == "default"
        assert register.call_args.kwargs["name"] == "aihub"

    def test_a_pymongo_connection_failure_is_not_mistaken_for_a_missing_alias(self):
        """mongoengine and pymongo each define a ConnectionFailure and they are unrelated classes. Only
        mongoengine's means "no such alias"; pymongo's means the server is unreachable and must propagate."""
        import pymongo.errors

        with (
            patch(f"{_MODULE}.mongoengine.connection.get_connection", side_effect=pymongo.errors.ConnectionFailure("down")),
            patch(f"{_MODULE}.register_connection") as register,
        ):
            with pytest.raises(pymongo.errors.ConnectionFailure):
                MongoConnectionRegistry.ensure_alias("researchdocs")

        register.assert_not_called()

    def test_an_unreachable_mongo_propagates_instead_of_being_mistaken_for_a_missing_alias(self):
        """The pipeline's old copy caught bare Exception here, so an outage failed later and more confusingly."""
        with (
            patch(f"{_MODULE}.mongoengine.connection.get_connection", side_effect=RuntimeError("network down")),
            patch(f"{_MODULE}.register_connection") as register,
        ):
            with pytest.raises(RuntimeError):
                MongoConnectionRegistry.ensure_alias("researchdocs")

        register.assert_not_called()
