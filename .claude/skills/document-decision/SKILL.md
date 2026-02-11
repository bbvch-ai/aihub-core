---
name: document-decision
description: Create Architecture Decision Records (ADRs) for significant technical
  decisions. Reviews changes, checks existing ADRs, and documents the "why" behind
  design choices.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write, Bash
---

# Document Architecture Decisions - Capture the "Why" Behind Your Design

Document significant technical decisions using ADRs (Architecture Decision Records).

Focus on: $ARGUMENTS

## Process

1. Review your changes against main
2. Check existing architecture decisions
3. Identify if you made significant architecture choices
4. Document new decisions properly
5. Reference any superseded decisions

## Step 1: Analyze Your Changes

```bash
git diff main...HEAD
git diff main...HEAD --name-only
```

Look for patterns suggesting architecture decisions: new packages/dependencies, new design patterns, major refactoring, changes to component communication, new technology integrations.

## Step 2: Review Existing Decisions

Read existing ADRs in `aihub_doc/arc42/decisions/` to understand prior decisions and check for conflicts.

## Step 3: Identify What Needs Documentation

**REQUIRES an ADR:**
- Technology choices (new framework, competing tech selection, new database)
- Architecture patterns (new design patterns, communication changes, new architecture styles)
- Major structural changes (package reorganization, component interaction changes, new layers)
- Cross-cutting concerns (security approaches, performance strategies, observability)
- Integration decisions (external systems, API versioning, data synchronization)

**Does NOT require an ADR:**
- Regular feature development following existing patterns
- Bug fixes and minor improvements
- Code quality improvements (type hints, test coverage, refactoring)

## Step 4: Write Your ADR

Create file in `aihub_doc/arc42/decisions/` with format: `YYYY_MM_DD_short_decision_summary.md`

Required structure:

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

## Quality Checklist

- Title clearly states the decision
- Context explains the "why" comprehensively
- Decision drivers are specific and measurable
- The decision is stated unambiguously
- Consequences include both pros and cons
- Any superseded decisions are referenced
