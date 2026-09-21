# Standard Agent Blueprints Are Curated by the Tenant Access Ceiling

## Context

A blueprint appears in Admin → Agents because a running agent answered a class-discovery request and the API wrote an
`AgentClassEntity` row. Nothing ever deletes those rows, and the row carries no visibility flag. So the catalog is the
union of every agent class the deployment has *ever* run — ten shipped blueprints on a normal install, plus whatever
playground classes a developer once started.

Product decided the standard set is three: Instructed Assistant (`LLMWrappingAgent`), Teachable Assistant
(`FewShotAgent`) and Document Intelligence Assistant (`RAGAgent`). Everything else should be absent at initial setup and
grantable afterwards, per customer.

Two mechanisms could express that, and only one is per-tenant. Not deploying the other seven is instance-wide, needs a
redeploy to undo, and cannot differentiate two customers sharing an instance — the same reasons
`2026_09_04_model_curation_as_tenant_ceiling_policy.md` rejected gateway removal for models. That ADR had already built
the alternative: a newly created tenant starts with a *derived* access ceiling rather than one `aihub.admin.>` wildcard.
Agents are the same problem one rule family over.

## Decision Drivers

1. **Curation must be reversible without a release.** Granting a customer an eighth blueprint should be an access-rule
   edit a sysadmin makes, not a compose change and a redeploy.
2. **Existing customers must not lose an agent they use.** Email Classification and Company Knowledge are deployed and
   in use; the change has to be inert for tenants that already hold a wildcard.
3. **Enumeration is what makes a row toggleable.** `locked = granted and rule not in granted_rules`, so under a single
   `agent.>` wildcard every blueprint renders locked and none can be unticked. Curation is impossible in the UI until
   the ceiling names classes individually.
4. **The seed must not depend on what happens to be running.** The startup tenant is seeded inside `initialize_db` at
   API boot, ~60s before the first agent answers discovery.

## Decision

**Enumerate the standard agent classes in the derived tenant ceiling, and filter the blueprint list by per-class
access.**

- **`DefaultTenantAccessRulesService` derives the agent family** from `AIHUB_TENANT_DEFAULT_ACCESS_AGENT_CLASSES`
  (default `LLMWrappingAgent,FewShotAgent,RAGAgent`) instead of emitting the fixed `aihub.admin.agent.>` it carried
  before. Like the model exclusions, the setting is a **seed read once**: afterwards the tenant's stored `access_rules`
  is the only authority, so granting a further blueprint later is an ordinary rule edit and the setting has no say.

- **Agents use an allow list where models use exclusions.** This inconsistency is deliberate. The model roster comes
  from LiteLLM, which is reachable at boot, and differs between CPU and GPU deployments — which is exactly why a
  hardcoded model list was rejected there. Neither holds for agents: class names are fixed at build time, and the
  discovered-class roster is still empty when the startup tenant is seeded, so an exclusion would have nothing to
  subtract from and would seed a tenant with no agents at all. Consequently the configured names are **not** validated
  against the roster: a class that has not been discovered yet is the normal case at boot, not an error.

- **One rule is emitted per class**, the bare `aihub.admin.agent.<Class>` and never `aihub.admin.agent.<Class>.>`. This
  reverses the two-rule form this ADR originally recorded, which granted each new tenant every existing profile of its
  standard blueprints — other tenants' included, because profiles share one global collection with no tenant column, so
  a subtree rule over a class is deployment-wide by construction (aihub-core-private#257). The bare root is what
  *creating* a profile is guarded on, and the profiles a tenant then creates are reached through
  `AgentService._grant_instance_access`, which grants each profile's own rule to the tenant that created it
  (`2026_06_15_auto_grant_creator_access_to_agent_instances`). The knowledge family still carries both forms, via
  `_CLASS_SUBTREE_POLICIES` below: a database's namespaces genuinely belong to the database, where a blueprint's
  profiles belong to whoever built them.

- **The blueprint checkbox grants the root and revokes the subtree — for agents only.** The catalog's class-level rows
  are generic machinery shared by every enumerable family, so this is expressed as a *per-family* policy
  (`_CLASS_SUBTREE_POLICIES` in `access_capability_service.py`) rather than as behaviour of the row: whether the
  wildcard under a class is the subject's to hold depends on whether the class owns what sits beneath it. A knowledge
  database owns its namespaces, so its row keeps writing and probing both forms; an agent class does not own the
  profiles built from it, so its `<Class>.>` moved to `Capability.revoked_rules` — written never, cleared always — and
  its `granted` became the root alone. A conjunction there would read a curated ceiling as not granted and bounce the
  box back when ticked. Untick still clears `<Class>.>` so a ceiling seeded under the old shape can be cleaned from the
  editor rather than by hand.

- **`GET /agents/classes` filters by `has_access_to_agent_class`,** which probes `aihub.user.agent.<Class>.?>`. The `?>`
  form matters: `?*` demands a rule strictly *below* the class, so it would hide every blueprint from a tenant holding
  only the bare roots — an empty Agents page with no way to add anything to it. Its route guard is the existence query
  `aihub.user.agent.?>`, which any single agent rule satisfies, so without this a curated tenant saw all ten cards and
  met the block only on click-through. The filter mirrors the sibling instances endpoint, which already narrows its
  result with `AccessChecker.from_user(user)`, and matches how the capability catalog already drops rows a ceiling
  cannot grant — "hidden, never merely disabled".

- **Curation applies to blueprints, never to templates within one.** A blueprint a tenant can see keeps every profile
  template it publishes; templates ride on the `AgentClassEntity` and the filter drops whole classes only.

## Consequences

### Positive

- Granting a blueprint to one customer is a tick in the sysadmin's tenant editor: no redeploy, no release, no role edit.
- Playground and other stale classes are curated out by the same mechanism, without a migration to delete their rows.
- All ten agents keep running and keep being built, so no customer loses an agent and no deployment topology changes.
- The blueprint list now agrees with the access catalog and the instances endpoint instead of being the one surface that
  ignored per-class access.

### Trade-offs

- **The ceiling is an enumerated snapshot.** A blueprint added to the standard set later does not reach tenants created
  earlier; a sysadmin grants it. For agents this is the intended opt-in behaviour, but it is the same limitation the
  model ADR records, and for the same reason: the rule grammar has no deny form.
- **Existing tenants are untouched** and keep `aihub.admin.agent.>`, so they still see every blueprint. Tenants seeded
  in the window where this ADR emitted both forms likewise keep `aihub.admin.agent.<Class>.>` and go on seeing every
  profile of those classes; nothing migrates them, and unticking the blueprint in the editor is the one-click cleanup.
  Two classes of tenant coexist until someone migrates the old ones — best done by the "apply standard set"
  tenant-editor action the model ADR already names as its own follow-up.
- **Rule hygiene is the only thing isolating profiles between tenants.** `agent_configs` has no tenant column, so any
  future `agent.>` rule re-opens the leak this reverses — the `aihub.admin.agent.>` access preset included. Giving the
  collection a real tenant discriminator is the durable fix and deserves its own decision.
- **All ten containers still run**, so the change saves no resources. Reducing the footprint would mean not deploying
  the optional agents, which is a separate decision with a redeploy as its only way back.
- **Two curation styles now live in one service** — an allow list for agents, exclusions for models. Justified above,
  but it is a thing a reader must be told rather than infer.
- **The subtree policy is the one piece of catalog behaviour not derived from the route guard.** Two families disagree
  about it and a third would have to choose deliberately; that is the price of a guard-derived catalog having nowhere to
  express ownership. A family added to `_CLASS_SUBTREE_POLICIES` inherits its entry for every class-level guard it
  gains, so a new guard in an existing family is not a neutral addition.
- **Hiding is not authorization.** Enforcement remains in the per-class route guards and the ceiling; the list filter is
  a UX consequence of them, and must not become the only barrier.

### Related Decisions

- `2026_09_04_model_curation_as_tenant_ceiling_policy.md` — established the derived ceiling this extends (premise)
- `2026_02_17_agent_profile_templates.md` — templates are what make a granted blueprint usable in two clicks
- `2026_04_15_sysadmin_implicit_admin_access.md` — why a sysadmin still sees every blueprint
- `2026_01_07_enable_dynamic_agent_configuration_ui.md` — the blueprint/profile split being curated here
