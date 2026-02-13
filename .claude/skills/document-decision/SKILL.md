---
name: document-decision
description: "Create Architecture Decision Records (ADRs) for significant technical
  decisions. Use when user says 'document this decision', 'create an ADR', 'record
  architecture decision', 'why did we choose X', 'document the rationale', or when
  adding major dependencies, new frameworks, or changing fundamental patterns.
  Reviews changes, checks existing ADRs, writes new ADR in arc42 format."
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write, Bash
---

# Document Architecture Decisions - Create ADRs

Create an Architecture Decision Record (ADR) to capture the "why" behind significant technical decisions. Takes an
optional focus topic as $ARGUMENTS.

## Steps

### 1. Analyze Your Changes

```bash
git diff main...HEAD
git diff main...HEAD --name-only
```

Look for patterns that indicate architecture decisions:
- New packages or dependencies added
- New design patterns introduced
- Major refactoring or restructuring
- Changes to component communication
- New technology integrations

### 2. Review Existing ADRs

Read existing ADRs in `aihub_doc/arc42/decisions/` to:
- Understand prior decisions and their rationale
- Check for conflicts or superseded decisions
- Maintain consistency in decision documentation

### 3. Determine If an ADR Is Needed

**REQUIRES an ADR**:
- Technology choices (new framework, database, competing tech selection)
- Architecture patterns (new design patterns, communication changes)
- Major structural changes (package reorganization, new layers)
- Cross-cutting concerns (security, performance, observability strategies)
- Integration decisions (external systems, API versioning)

**Does NOT require an ADR**:
- Regular feature development following existing patterns
- Bug fixes and minor improvements
- Code quality improvements (type hints, test coverage, refactoring)

### 4. Write the ADR

Create file in `aihub_doc/arc42/decisions/` with naming format: `YYYY_MM_DD_short_decision_summary.md`

**Required structure**:

```markdown
# Title of the Decision

## Context
Describe the problem or situation that necessitates this decision.

## Decision Drivers
- Key force 1
- Key force 2

## Decision
State your decision clearly and unambiguously.

## Consequences
Both positive outcomes and negative trade-offs.
```

### 5. Cross-Reference

- If this decision supersedes a previous ADR, reference it explicitly
- If other ADRs are related, add cross-references

## Examples

**Typical invocation**:
```
/document-decision switching from Redis to Valkey
```

**ADR filename**: `2026_02_13_switch_from_redis_to_valkey.md`

**Example Context section**:
> We need a Redis-compatible in-memory store that is fully open-source and actively maintained after the Redis license
> change. Valkey is a community fork maintaining Redis v5 API compatibility.

## Quality Checklist

Before marking complete, verify:

- [ ] Title clearly states the decision (not the problem)
- [ ] Context explains the "why" comprehensively
- [ ] Decision drivers are specific and measurable
- [ ] Decision is stated unambiguously
- [ ] Consequences include both pros and cons
- [ ] Superseded decisions are referenced (if any)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Unsure if change warrants an ADR | If you debated between two approaches, it likely warrants one |
| Existing ADR covers similar ground | Update the existing ADR rather than creating a duplicate |
| Decision affects multiple scopes | Document once in the central ADR directory, not per-scope |
| Cannot determine decision drivers | Review git log and PR discussions for the original reasoning |
