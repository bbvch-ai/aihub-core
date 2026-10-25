from swiss_ai_hub.backup.services.psql_script import PsqlScript

_GLOBALS_DUMP = """--
-- PostgreSQL database cluster dump
--

\\restrict slBtgy3q7M3JfyZyrDZV7A0k1Mmwl3TLGYsnnGqc3SpJrTsBdHxirqzQABZkmHI

SET default_transaction_read_only = off;
CREATE ROLE admin;
ALTER ROLE admin WITH SUPERUSER INHERIT LOGIN PASSWORD 'SCRAM-SHA-256$4096:abc=$def=:ghi=';
CREATE ROLE "Mixed-Case";
COMMENT ON ROLE admin IS 'CREATE ROLE inside a comment;';
GRANT pg_read_all_data TO admin WITH INHERIT TRUE GRANTED BY admin;

\\unrestrict slBtgy3q7M3JfyZyrDZV7A0k1Mmwl3TLGYsnnGqc3SpJrTsBdHxirqzQABZkmHI
"""


def test_restricted_locks_meta_commands_with_a_fresh_key() -> None:
    first = PsqlScript.restricted("SELECT 1;\n")
    second = PsqlScript.restricted("SELECT 1;\n")

    first_line = first.splitlines()[0]
    assert first_line.startswith("\\restrict ")
    assert len(first_line.removeprefix("\\restrict ")) == 64
    assert first_line != second.splitlines()[0]


def test_restricted_drops_the_dumps_own_restrict_pair() -> None:
    script = PsqlScript.restricted(_GLOBALS_DUMP)

    assert "slBtgy3q7M3JfyZyrDZV7A0k1Mmwl3TLGYsnnGqc3SpJrTsBdHxirqzQABZkmHI" not in script
    assert "\\unrestrict" not in script
    assert script.count("\\restrict ") == 1


def test_restricted_keeps_a_planted_unrestrict_or_shell_escape_as_inert_text() -> None:
    planted = "SELECT 1;\n\\unrestrict guessed\n\\! id\n"

    script = PsqlScript.restricted(planted)

    assert script.startswith("\\restrict ")
    assert "\\! id" in script
    assert "\\unrestrict guessed" not in script


def test_tolerating_existing_roles_wraps_only_bare_create_role_lines() -> None:
    script = PsqlScript.tolerating_existing_roles(_GLOBALS_DUMP)

    assert "DO $restore$ BEGIN CREATE ROLE admin; EXCEPTION WHEN duplicate_object THEN NULL; END $restore$;" in script
    assert (
        'DO $restore$ BEGIN CREATE ROLE "Mixed-Case"; EXCEPTION WHEN duplicate_object THEN NULL; END $restore$;'
        in script
    )
    assert "\nCREATE ROLE admin;\n" not in script
    assert "ALTER ROLE admin WITH SUPERUSER" in script
    assert "COMMENT ON ROLE admin IS 'CREATE ROLE inside a comment;';" in script


def test_with_boolean_setval_flags_rewrites_psql_unaligned_booleans() -> None:
    catalog = (
        "SELECT setval('documentdb_api_catalog.collections_collection_id_seq', 12, t);\n"
        "SELECT setval('documentdb_api_catalog.collection_indexes_index_id_seq', 1, f);\n"
    )

    script = PsqlScript.with_boolean_setval_flags(catalog)

    assert "SELECT setval('documentdb_api_catalog.collections_collection_id_seq', 12, true);" in script
    assert "SELECT setval('documentdb_api_catalog.collection_indexes_index_id_seq', 1, false);" in script


def test_with_boolean_setval_flags_leaves_current_format_unchanged() -> None:
    catalog = "SELECT setval('documentdb_api_catalog.collections_collection_id_seq', 12, true);\n"

    assert PsqlScript.with_boolean_setval_flags(catalog) == catalog
