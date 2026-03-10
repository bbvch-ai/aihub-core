---
name: document-decision
description: Create Architecture Decision Records (ADRs) in docs/arc42/decisions/. Use when user says 'document this decision', 'create an ADR', 'record architecture decision', 'why did we choose X', 'document the rationale', or when adding major dependencies, new frameworks, or changing fundamental patterns. Do NOT use for user-facing feature docs (use /document-feature) or syncing existing docs (use /update-doc).
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

# Document Architecture Decisions - Create ADRs

Create an Architecture Decision Record (ADR) to capture the "why" behind significant technical decisions. Takes an
optional focus topic as \$ARGUMENTS.

Root CLAUDE.md defines when ADRs are required (major dependencies, new frameworks, fundamental pattern changes). This
skill handles the creation workflow.

## Before You Start

Read these files for context:

- **Template**: `docs/arc42/decisions/0000_00_00_template.md` — the required ADR structure (Context, Decision Drivers,
  Decision, Consequences)
- **Exemplar**: `docs/arc42/decisions/2026_02_10_replace_phoenix_with_langfuse.md` — a well-written ADR with detailed
  decision drivers, specific consequences split into positive and trade-offs
- **Existing ADRs**: Browse `docs/arc42/decisions/` (14 ADRs as of Feb 2026) to check for conflicts or decisions to
  supersede

## Step 1: Analyze Changes

```bash
git diff --name-only main...HEAD
git diff --stat main...HEAD
```

Identify which architectural choice was made and what alternatives were considered.

## Step 2: Check for Existing ADRs

```bash
ls docs/arc42/decisions/
```

Read any ADR that covers similar ground. If one exists, update it rather than creating a duplicate.

## Step 3: Create the ADR File

**Filename**: `docs/arc42/decisions/YYYY_MM_DD_short_decision_summary.md`

- Date: today's date with underscores (`2026_02_19`)
- Summary: lowercase with underscores (`adopt_valkey_for_caching`)
- Convention follows existing files like `2026_02_10_replace_phoenix_with_langfuse.md`

**Content**: Follow the template at `docs/arc42/decisions/0000_00_00_template.md`. The four required sections:

1. **Context** — the problem or situation, referencing specific Swiss AI Hub components (NATS, Milvus, Dagster, LiteLLM,
   etc.)
2. **Decision Drivers** — each driver as a bold label with explanation (see the Langfuse ADR for format)
3. **Decision** — what was decided and how it applies to this codebase's architecture
4. **Consequences** — split into "Positive" and "Trade-offs" subsections when there are many

If this decision supersedes a previous ADR, reference it explicitly in the Context section.

## Step 4: Verify

```bash
# File exists in the right location
ls docs/arc42/decisions/$(date +%Y_%m_%d)_*.md

# Has all four required sections
grep -c '^## ' docs/arc42/decisions/$(date +%Y_%m_%d)_*.md
# Should be ≥ 4 (Context, Decision Drivers, Decision, Consequences)
```

## Troubleshooting

| Problem                            | Solution                                                             |
| ---------------------------------- | -------------------------------------------------------------------- |
| Unsure if change warrants an ADR   | If you debated between two approaches, it likely warrants one        |
| Existing ADR covers similar ground | Update the existing ADR with `Edit` rather than creating a duplicate |
| Decision affects multiple scopes   | Document once in `docs/arc42/decisions/`, not per-scope              |
