# Agent-Config Secrets Are Decrypted at Validation

## Context

Agent profiles hold credentials: the mailbox password and Entra ID client secret of the IMAP and email-classification
agents, the API key of an MCP connection, the Jira token of the release notes agent. Until #1587 they were stored in
plaintext in `agent_configs`, returned in every API response that carried the profile, sent in plaintext over the NATS
config RPC, and kept in plaintext in the run's RunContext in Valkey. ADR `2026_07_05_agent_imap_read_capability` and ADR
`2026_09_23_imap_oauth2_app_only_auth` accepted that as a follow-up.

Knowledge source configurations already encrypt their secrets (#1861, `SecretEncryptionService`, ADR
`2026_09_14_secret_mask_carries_identity_handle`): the API encrypts on write and masks on read, and the pipeline
decrypts when it builds the source. #2263 added the refusal of submitted ciphertext.

## Decision Drivers

- **Only ciphertext outside the step**: the database, the RPC reply, RunContext and Valkey must never hold plaintext.
- **No field names in code**: secrets are found through the announced form, as for knowledge sources.
- **Nothing breaks without a secret**: blueprints without secret fields, and profiles that leave them blank, must keep
  working on a deployment that has no key.
- **No silent damage**: a missing key must not make the platform drop profiles or delete their OpenWebUI models.

## Decision

1. **Secret paths come from the class form.** `AgentConfig.secret_field_paths()` walks `as_form()` for `Password` and
   `SecretFileInput` elements, mirroring `SourcePipelineConfig.secret_field_paths()`. Many configs (playground ones
   among them) do not override `as_form()` and cannot build a form, so the paths are only ever computed lazily.
2. **The API encrypts on create and update** (`ConfigSecrets`, `packages/api/.../util/config_secrets.py`). Masks are
   restored against the stored row before validation; on create there is no stored row, so a mask carried over by a
   clone or an import is a 400. Submitted ciphertext is refused with `reject_submitted_ciphertext` from #2263, and the
   update's validation 400 leaves out the input, since by then it holds the restored ciphertext.
3. **The API masks in one place**, `FullAgentInstanceDTO.from_class_and_config`, which every response holding a profile
   goes through: get, list, list-by-class, create, update, `/mcp` and the Admin UI export.
4. **The RPC stays unmasked and ciphertext travels.** `get_agent_configuration` returns the stored, encrypted row; the
   dispatcher stores it in RunContext as it is. `AgentDispatcher._decrypted` decrypts only right before
   `model_validate`, and only at the secret paths; ciphertext anywhere else stays inert. When no value carries the
   ciphertext prefix the config passes through unchanged and no form is built, so an agent without encrypted values
   needs neither the key nor a form.
5. **The key goes to three agent containers**: `imap_agent`, `email_classification_agent` and `release_notes_agent`,
   next to the API and the pipelines. A template comment names every blueprint with a `Password` field, including
   `mcp_react_agent`, which has no compose service.
6. **A permanent startup guard, and a transitional migration.** Masking needs a usable key, and the key is needed only
   when a non-empty string sits at a secret path (`ConfigSecrets.has_secret_values`, the single condition for masking,
   encrypting and the guard). `ConfigSecrets.ensure_key_for_stored_secrets` runs in the lifespan right after the Mongo
   connection, before the config responder and discovery start, and refuses to start the API when a profile holds such a
   value and the key is unset or malformed. Together the two make masking unable to raise at runtime, so
   `InstanceDtoBuilder.build_or_skip` never drops a profile and the OpenWebUI sync never deletes its model; internal
   callers therefore keep using `FullAgentInstanceDTO` unchanged. Separately, `PlaintextAgentSecretMigration`, wired
   with the other transitional migrations, encrypts the profiles stored before #1587 with a compare-and-swap write.
7. **Clone and import clear masks in the Admin UI** and name the cleared fields in a toast. The export is unchanged: it
   already holds masks, which is what lets the import detect them.

## Consequences

- **Rollout order**: agent images first or in the same deployment, the API last. An agent from before #1587 receiving
  ciphertext would use it as its credential. Custom SDK agents with `Password` fields must upgrade and receive the key
  before the API.
- **The API refuses to start** for every tenant while a non-empty secret is stored and the key is missing or a
  placeholder. This is intended; the release note says so.
- **A wrong but well-formed key** lets the API start and mask; agent runs then fail with Fernet's generic `InvalidToken`
  as an `ExceptionEvent`, and saves whose handles no longer match get a 400 asking to resubmit the form.
- **No key rotation**, as for knowledge sources. Backups restore usable secrets only with the key in use when they were
  taken.
- **Forms open during the upgrade** that hold a mask minted from plaintext get a 400 "resubmit the form" once the
  migration has encrypted the row.
- **Already leaked**: exports made before the upgrade, Langfuse spans, plaintext RPC history and backups. The IMAP, MCP
  and Jira credentials should be rotated.
- **Known gap, step-span inputs**: `AgentRunTracer.trace_step_start` serialises step kwargs into Langfuse, so decrypted
  `ImapClientConfig`, `McpClientConfig` and `JiraConnectionConfig` values, and whole `AgentConfig` kwargs, still reach
  step spans. That was true before #1587 and is left to a follow-up issue, together with error-status redaction,
  `hide_input_in_errors` on `AgentConfig` and a readable wrong-key message. Valkey holds no decrypted config. Langfuse's
  queue holds pointers, not span bodies (inferred, not verified).
- **FormKit numbered-dict repeaters**: `SecretPathTransformer` and `reject_submitted_ciphertext` walk lists only. No
  agent secret sits in a repeater today.
