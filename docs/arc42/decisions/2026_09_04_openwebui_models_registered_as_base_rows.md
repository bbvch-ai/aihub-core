# OpenWebUI Models Are Registered As Base Rows, Not Presets

## Context

Bumping OpenWebUI from `0.9.5` to `0.11.3` (`compose-config.yml`, branch `chore/openwebui-0.11.3`) broke chat for every
non-admin user on every model — agent-backed and raw LLM alike:

```
2026-09-02 08:06:55 | WARNING | open_webui.main:chat_completion:1618 - Error processing chat metadata: Model not found
"POST /api/chat/completions HTTP/1.1" 400
```

The model was visible in the picker, admins could chat with it, and the OpenWebUI database had zero base-model override
rows — the state the provisioner is supposed to maintain. Reading the running container's own source
(`utils/access_control/__init__.py::has_base_model_access`) found the actual change between the two versions:

```python
base_model_info = await Models.get_model_by_id(base_model_id, db=db)
if base_model_info is None:
    return user_role == 'admin'      # 0.11.3. Was `return True` in 0.9.5.
```

`OpenWebuiProvisioner` (`packages/core/swiss_ai_hub/core/infrastructure/openwebui/openwebui_provisioner.py`, ADR
`2026_03_05_aihub_manages_openwebui_model_visibility.md`) was built entirely around the *old* meaning of an unregistered
base: every provisioned model was a preset (`aihub-agent-{class}-{id}`, `aihub-model-{capability}-{name}`) whose
`base_model_id` pointed at a raw id (`aihub-pipeline.{class}.{id}`, `{capability}/{name}`) that
`_delete_shadowing_base_models` actively kept unregistered — on the explicit assumption that a registered base entry
would deny non-admin access to everything above it. 0.11.3 makes the opposite true, and that method was re-asserting the
now-broken state on every sync.

Every mechanism below was confirmed against a real running OpenWebUI instance, not inferred from source alone:

- Creating a base-registry row directly on a raw LLM id (no `base_model_id`), granting one group read access, and
  chatting as a non-admin member of that group returned `200`; clearing the grant reproduced the original `400`.
  Identical result for a raw agent-pipe id against a genuinely online agent instance.
- Restarting the local API — which runs `OpenWebuiProvisioner.provision()` on startup — with the fix applied deleted
  every legacy preset row from the live database and replaced them with base rows carrying real, role-derived grants; a
  non-admin user then chatted the real (not synthetic) production rows successfully.
- `OpenWebuiClient.update_model_access` was separately found to send `access_grants: null` whenever the computed grant
  list was empty, and OpenWebUI's update endpoint treats a null list as "leave existing grants untouched" — so a role or
  tenant-ceiling change that revokes a group's last grant on a model was silently not taking effect. Unrelated to the
  version bump, found while instrumenting the same code path.

A patch to the OpenWebUI fork (reverting the one line above) was considered and rejected: the project does not maintain
a divergent OpenWebUI fork, and every fix here had to live in `packages/core`.

## Decision Drivers

- **No fork patches.** The platform does not maintain a patched OpenWebUI image; the fix must be entirely within the
  provisioner.
- **The existing gating design stays intact.** Tenant ceilings, role rules, and `AccessChecker` must keep working
  exactly as before — this is a change to *where* a grant is registered, not to how access is computed.
- **One picker entry per model.** An alternative (keep the preset, additionally register its base with the union of the
  preset's grants) was built and tested live: it left two picker entries per model (the preset and its now-visible
  base), which is a worse outcome than the bug being fixed. `is_active: False` on the base does not hide it either — it
  removes the row for every viewer, admin included, since `get_all_models` filters it out unconditionally — and doing so
  also drops it from `app.state.MODELS` entirely, so the preset it backs 404s instead of merely mis-gating.
- **The picker and the chat check must not be allowed to disagree.** Reading `utils/models.py::get_filtered_models`
  confirmed the non-admin picker filter checks only the model's own grant, never its base chain — so a preset can be
  visible while its base silently denies chat. Collapsing preset and base into one row removes this class of bug rather
  than working around its current symptom.
- **The escalation 0.11.3 guards against does not exist in this deployment.** The admin-only fallback exists so an
  unregistered base cannot be reached through a preset by someone who could not use the raw model directly. Here,
  `get_filtered_models` already hides row-less raw models from every non-admin — a managed row is the *only* path a
  non-admin ever has to a raw model, so the guard has nothing to protect against in this design.

## Decision

**Every provisioned model — agent-backed or raw LLM — is registered as a single base-registry row on its own raw id,
carrying its own access grants directly, instead of a preset pointing at an unregistered base one hop above it.**

1. **Row construction changed to emit the raw id, with no `base_model_id`.** An agent's row id is
   `aihub-pipeline.{agent_class}.{agent_id}` (previously the *base* of a separate `aihub-agent-{class}-{id}` preset); an
   LLM row id is `{capability}/{name}` (previously the base of `aihub-model-{capability}-{name}`). A
   `meta.aihub_managed = True` marker distinguishes a provisioner-owned row from one a human created directly in the
   OpenWebUI workspace, so a sync never overwrites or deletes the latter.
2. **Reconciliation reads `list_base_models`, never `list_models`.** OpenWebUI's model search filters on
   `base_model_id != None`, so any row shaped like the ones above — and the Workspace UI built on that same search —
   cannot see them; `GET /models/base` is the only way. All three sync methods (workspace models, LLM models, access
   grants) switched accordingly, filtered by the managed marker and, where both row kinds share one listing, by the
   `aihub-pipeline.` id prefix to keep them from colliding in the same diff.
3. **`_delete_shadowing_base_models` is deleted, not repaired.** Its purpose — deleting a base-registry entry because
   its mere existence was assumed dangerous — is exactly the inverted assumption; keeping it to do the opposite under a
   new name would just relocate the same coupling. Grant computation and id parsing now dispatch on the row's own id
   shape instead of a `base_model_id` that no longer exists on any managed row.
4. **A one-time migration removes the pre-0.11.3 preset rows.** `_delete_legacy_preset_models` runs on every access sync
   (every entry point funnels through `_sync_access_grants`) rather than once, since there is no reliable one-shot hook
   across replicas; it is a no-op once no legacy-prefixed id remains. Both legacy prefix constants and this method are
   commented as removable one release after this ships.
5. **`TASK_MODEL`/`TASK_MODEL_EXTERNAL` now name the raw model id directly.** They previously had to name the workspace
   preset id: OpenWebUI's background-task calls (chat titles, follow-up questions) run under the end user's own identity
   and hit the same access check as chat, so naming the raw id used to be denied outright for anyone without the
   preset's grant. With the preset layer gone, the raw id is simultaneously the routable id and the one carrying the
   grant, so the two settings converge on the same value as `OPENWEBUI_CONVERSATION_METADATA_MODEL`.
6. **The independently found grant-revocation bug is fixed alongside this.** `OpenWebuiClient.update_model_access` now
   always sends the computed grant list verbatim, including empty, instead of substituting `null` — which OpenWebUI's
   update endpoint reads as "leave existing grants untouched."

## Consequences

### Positive

- The reported failure (every non-admin denied chat on every model) is fixed, verified against the real dev-stack
  database and a genuinely online agent — not only by unit test.
- Picker visibility and chat access are now backed by the same row, so a model can no longer be shown as usable and then
  deny the chat request.
- One entry per model in the OpenWebUI Workspace and picker; no duplicate raw/preset pair.
- The grant-revocation bug is closed as a side effect — a role or tenant-ceiling change that drops a group's access to
  zero now actually clears the stale grant, independent of the version-bump work that surfaced it.
- No OpenWebUI fork required; the fix is entirely within `packages/core`.

### Trade-offs

- **A managed row is invisible to the OpenWebUI Workspace UI.** Only `GET /models/base` sees it; an admin cannot browse
  or hand-edit these rows through the normal Workspace screen, so diagnosing a provisioning problem now requires the API
  or database rather than the UI.
- **The legacy-preset migration runs on every sync indefinitely**, until someone removes it by hand. Cheap once there is
  nothing left to migrate, but it is dead code carried forward with only a comment — not a mechanism — reminding that it
  should go.
- **The whole fix rests on undocumented OpenWebUI internals**, not a published contract: `has_base_model_access` and the
  base-row/preset distinction were both reverse-engineered by reading the running container's source. A future OpenWebUI
  release could change this again without any changelog entry, exactly as `0.11.3` did here.
- **Agent-row registration was verified against a single online agent class.** The id-construction mechanism
  (`aihub-pipeline.{class}.{id}`) is identical for every agent class — it matches OpenWebUI's own manifold id
  construction in `functions.py` (`f'{pipe.id}.{p["id"]}'`) — but only one class was actually online to confirm live.
- **`TASK_MODEL` and `OPENWEBUI_CONVERSATION_METADATA_MODEL` now always carry the same value** where they previously
  differed by a string transform. They remain two separate settings, read by two different consumers, on the expectation
  that a future change could make them diverge again — not collapsed into one.
