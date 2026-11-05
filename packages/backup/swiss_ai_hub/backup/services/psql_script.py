import re
import secrets

_DUMP_RESTRICT_LINE_RE = re.compile(r"^\\(?:un)?restrict [A-Za-z0-9]+$", re.MULTILINE)
_CREATE_ROLE_LINE_RE = re.compile(r'^CREATE ROLE ("(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_$]*);$', re.MULTILINE)
_SETVAL_LINE_RE = re.compile(r"^(SELECT setval\('[\w.]+', \d+), ([tf])\);$", re.MULTILINE)


class PsqlScript:
    """Prepares SQL read from a backup artifact so psql executes it as plain SQL only.

    The artifact comes from shared object storage, so it is untrusted input. A random `\\restrict` key that the
    script cannot know disables every psql meta-command (`\\!`, `\\copy`, `\\o`, ...) for the rest of the session,
    and `ON_ERROR_STOP` makes the first failing statement fail the restore instead of being skipped.
    """

    PSQL_OPTIONS: tuple[str, ...] = ("-X", "-v", "ON_ERROR_STOP=1")

    @staticmethod
    def restricted(sql: str) -> str:
        """Drop the dump's own restrict/unrestrict pair and lock meta-commands with a key generated here."""
        body = _DUMP_RESTRICT_LINE_RE.sub("", sql)
        return f"\\restrict {secrets.token_hex(32)}\n{body}"

    @staticmethod
    def tolerating_existing_roles(globals_sql: str) -> str:
        """Make `pg_dumpall --globals-only` output re-runnable on a cluster whose roles survive the restore.

        pg_dumpall emits a bare `CREATE ROLE` for every role, including the one restoring, and relies on the
        following `ALTER ROLE` to set its attributes; only the duplicate is ignored, any other error still stops.
        """
        return _CREATE_ROLE_LINE_RE.sub(PsqlScript._create_role_unless_exists, globals_sql)

    @staticmethod
    def _create_role_unless_exists(match: re.Match[str]) -> str:
        """The dollar tag must not occur in the role name, or a quoted name such as "app$restore$" ends the body."""
        role = match.group(1)
        tag = "restore"
        while f"${tag}$" in role:
            tag += "_"
        return f"DO ${tag}$ BEGIN CREATE ROLE {role}; EXCEPTION WHEN duplicate_object THEN NULL; END ${tag}$;"

    @staticmethod
    def with_boolean_setval_flags(catalog_sql: str) -> str:
        """Rewrite psql's unaligned `t`/`f` booleans, which older catalog artifacts wrote verbatim into setval()."""
        return _SETVAL_LINE_RE.sub(
            lambda match: f"{match.group(1)}, {'true' if match.group(2) == 't' else 'false'});",
            catalog_sql,
        )
