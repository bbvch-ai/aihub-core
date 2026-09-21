---
name: sync-agent-docs
description: Bring an agent's user-facing documentation page under docs/docs/2_platform/5_agents/ back in line with its implementation. Nothing textually links a doc page to the code behind it, so this drift is invisible to grep and to the generic doc sweeps. Run it whenever a change lands in packages/agent/swiss_ai_hub/agent/{agents,imap,rag,mcp,steps}/, packages/agent/app/<agent>/, or an agent config model under packages/core/swiss_ai_hub/core/ -- especially for a feat( commit, which by definition adds behaviour a user-facing page should describe. Use when user says 'the agent docs are out of date', 'sync agent documentation', 'document the new email agent features', 'did the docs keep up with this agent', or after implementing any agent capability, config field or limit. Do NOT use for writing a brand-new agent page from scratch (use document-feature), the generic README/CLAUDE.md staleness sweep (use update-doc), or ADRs (use document-decision).
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# Sync Agent Docs

Each production agent has a user-facing page under `docs/docs/2_platform/5_agents/`. This skill finds the page for the
agent you changed, works out what the page no longer says, and fixes it.

## Why this drift is invisible

The agent pages are written for end users, so they **never name the implementation class**. `11_email_agent` does not
contain the string `ImapAgent`; `10_company_knowledge_agent` does not contain `ExpertRAGAgent`. There is no import, no
path reference, no shared identifier.

So every ordinary staleness heuristic misses them. `grep -rl "$(basename "$f")" docs/` finds nothing. `/update-doc`'s
sweep is driven by exactly that kind of name match. The page can sit untouched for months while its agent gains feature
after feature, and no tool reports a thing.

`packages/agent/CLAUDE.md` stays current because developers editing the code read it. The user-facing page has no such
reader until a customer hits it.

## Step 0: Which agent changed?

```bash
BASE=$(git merge-base HEAD origin/main)
git diff --name-only "$BASE"...HEAD | grep -E \
  "^(packages/agent/(swiss_ai_hub/agent/(agents|imap|rag|mcp|steps)/|app/)|packages/core/swiss_ai_hub/core/imap/)" \
  || echo "no agent-implementation change -- stop here"
```

No match means no agent page can have gone stale from this diff. Say so and stop.

Note what the paths imply: an agent's doc-relevant code is **not** confined to its own directory.

## Step 1: Map code to doc page

The join key is the display name. `packages/agent/swiss_ai_hub/agent/i18n/translations/agent/<module>.en.yml` has a
top-level `name:` that equals the doc page's `title:`. Derive it rather than trusting the table below:

```bash
for f in packages/agent/swiss_ai_hub/agent/i18n/translations/agent/*.en.yml; do
  printf "%-28s :: %s\n" "$(basename "$f" .en.yml)" "$(grep -m1 -E '^  name:' "$f" | sed 's/^  name: *//')"
done
```

Current mapping — note that code names and product names have almost nothing in common:

| Doc page                            | Agent module (`agents/…`)    | Also reads from                       |
| ----------------------------------- | ---------------------------- | ------------------------------------- |
| `3_instructed_assistant`            | `llm_wrapping_agent`         |                                       |
| `4_teachable_assistant`             | `few_shot_agent`             | `agent/steps/`                        |
| `5_document_intelligence_assistant` | `rag_agent`                  | `agent/rag/`, `agent/self_awareness/` |
| `6_retrieval_agent`                 | `retrieval_agent`            | `agent/rag/`                          |
| `7_document_navigation_assistant`   | `namespace_selection_agent`  |                                       |
| `8_mcp_tool_agent`                  | `mcp_react_agent`            | `agent/mcp/`                          |
| `9_expert_coordinator_agent`        | `expert_asking_agent`        |                                       |
| `10_company_knowledge_agent`        | `expert_rag_agent`           | `agent/rag/`                          |
| `11_email_agent`                    | `imap_agent`                 | `agent/imap/`, `core/imap/`           |
| `12_email_classification_agent`     | `email_classification_agent` | `agent/imap/`, `core/imap/`           |

**Two exceptions the derivation cannot give you.** `imap_agent` and `memory_writer_agent` have no i18n file, so they are
absent from the loop's output. `imap_agent` is `11_email_agent`. `memory_writer_agent` is a non-discoverable system
agent with no user-facing page and needs none.

`1_fundamentals` and `2_blueprints_and_profiles` are concept pages, not per-agent pages. They go stale when the
framework changes (`agent/workflow/`, `agent/dispatchers/`, `agent/runners/`), not when one agent does.

## Step 2: Measure the drift

```bash
DOC=docs/docs/2_platform/5_agents/11_email_agent/          # the page
CODE=(packages/agent/swiss_ai_hub/agent/agents/imap_agent/ \
      packages/agent/swiss_ai_hub/agent/imap/ \
      packages/agent/app/imap_agent/ \
      packages/core/swiss_ai_hub/core/imap/)               # everything it describes

SHA=$(git log -1 --format=%H -- "$DOC")
echo "doc last touched: $(git log -1 --format='%ad  %s' --date=short -- "$DOC")"
git log --format="%h %ad %s" --date=short "$SHA"..HEAD -- "${CODE[@]}"
```

Every `feat(` line is a candidate gap — a feature shipped after the page was last written. `fix(` lines matter when they
change documented behaviour, a default, or a limit.

## Step 3: Check the page against the code

Read the page, then verify each of these against the implementation. They are where drift actually lands:

- **Config tables.** Agent pages carry a field-by-field table (field, type, default, description). It must match the
  config model — including nested groups. These models often live in `packages/core`, not in the agent package:
  `ImapAgentConfig` nests `ImapClientConfig` and `DraftEmailSettings` from `core/imap/`. A field added there changes the
  Admin UI form and the doc table while touching nothing under `packages/agent/`. Check a field's presence in the
  *rendered* form, not just the model — `as_form()` deliberately withholds fields (see `ImapAgentConfig._draft_form`),
  and a field the admin never sees must not appear in the table.
- **Capability sections.** One section per user-visible capability. New `@step` chains, new start events and new
  triggers usually mean a new section or a changed flow diagram.
- **Mermaid diagrams.** A new branch in the workflow is a new branch in the diagram.
- **Limits and defaults.** Message sizes, batch sizes, token budgets, timeouts. These are stated as concrete numbers and
  silently rot when a constant moves.
- **"What it does *not* do" claims.** The highest-risk section in the file. `11_email_agent` promises "there is no SMTP
  anywhere in it". A negative claim that goes stale is worse than a missing feature — verify each one still holds.

## Step 4: Write the update

Match the existing page. These are **user-facing** docs on the VitePress site, not developer notes:

- No class names, module paths, event types or step-function names. The reader is an admin configuring the agent.
- Keep the page's own voice and structure — `:::tip` / `:::warning` containers, tables, mermaid. Do not impose a
  template; see `/document-feature` for the house style.
- Describe what the agent now *does for the user*, not how it was implemented.
- Never state a capability you have not confirmed in the code. A commit subject is a hint, not a specification — read
  the diff.

**Update every locale the page already has.** These pages are `index.en.md` + `index.de.md`, written in lockstep and
committed together. Shipping only the English leaves the German silently wrong, which is worse than leaving it visibly
old. If you cannot write the German, say so explicitly rather than quietly skipping it.

If the change is framework-level rather than agent-level, the developer-facing pages under
`docs/docs/3_sdk/2_building_agents/` may also need it — and `packages/agent/CLAUDE.md` is a separate concern from the
docs site.

## Sweep mode

To find every stale page rather than the one you just changed, iterate the Step 1 table through Step 2.

Snapshot taken **2026-09-18** (doc date, `feat(` commits since, total commits since):

| Doc page                            | Last doc update | feats behind | commits behind |
| ----------------------------------- | --------------- | ------------ | -------------- |
| `10_company_knowledge_agent`        | 2026-06-08      | 10           | 17             |
| `4_teachable_assistant`             | 2026-06-01      | 8            | 15             |
| `3_instructed_assistant`            | 2026-06-01      | 8            | 13             |
| `8_mcp_tool_agent`                  | 2026-06-02      | 7            | 9              |
| `7_document_navigation_assistant`   | 2026-06-01      | 5            | 7              |
| `11_email_agent`                    | 2026-08-13      | 6            | 8              |
| `9_expert_coordinator_agent`        | 2026-06-08      | 3            | 3              |
| `6_retrieval_agent`                 | 2026-06-02      | 3            | 3              |
| `5_document_intelligence_assistant` | 2026-09-15      | 0            | 2              |
| `12_email_classification_agent`     | 2026-09-07      | 1            | 1              |

Recompute before relying on it — it is a starting backlog, not a live view. Treat each page as its own change; a sweep
that rewrites ten pages in one PR is unreviewable.

## Worked example: the email agent

`11_email_agent` was last updated 2026-08-13 (#1727). Since then the IMAP code took 8 commits, 6 of them `feat(`. The
page mentions attachments six times but contains no occurrence of `PDF`, `scan`, `OCR`, `.eml`, `data lake` or `archiv`
— so at minimum:

- **#1871** attachment text extraction from PDFs, scans and `.eml` — undocumented
- **#1730** archiving the original message in the data lake — undocumented
- **#1711** creating a missing IMAP target folder when filing — mentioned once, worth verifying against the code

That is the shape of the problem this skill exists to catch.

## Done when

- The page describes every user-visible capability the agent currently has
- The config table matches the rendered form, nested groups included
- Limits, defaults and negative claims verified against the code
- Every locale of the page updated together
- Nothing asserted that is not in the implementation
