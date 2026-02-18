---
name: create-or-audit-claude-md
description: >
  Audits an existing CLAUDE.md or builds one from scratch by analyzing the
  actual codebase — config files, git history, CI/CD, existing docs, and code
  patterns. Use when user says "audit our CLAUDE.md", "improve our CLAUDE.md",
  "build a CLAUDE.md", "is our CLAUDE.md good", "what's missing from our
  CLAUDE.md", or "bootstrap CLAUDE.md". Also use when user says "onboard Claude
  to this repo" or "set up Claude Code for this project". Do NOT use for
  writing skills (use audit-skill instead) or for general documentation tasks.
allowed-tools: Bash(find:*) Bash(grep:*) Bash(git:*) Bash(cat:*) Bash(head:*) Bash(wc:*) Bash(ls:*) Bash(jq:*) Read Write Edit Grep Glob
---

# Audit or Build CLAUDE.md from Codebase Evidence

You are performing codebase archaeology. Your job is to discover what conventions, patterns, and workflows ALREADY EXIST
in this codebase and either verify that the current CLAUDE.md captures them, or produce a new one that does. You are NOT
inventing new standards — you are extracting established ones.

## Principles

1. **Evidence over opinion.** Every line you propose for CLAUDE.md must trace to something observable in the codebase: a
   config file, a git pattern, a CI pipeline, existing documentation, or a repeated code pattern.

2. **Less is more.** A CLAUDE.md under 150 lines that Claude follows perfectly beats a 500-line file where critical
   rules get lost. The root file should only contain what applies to >30% of sessions.

3. **Don't duplicate tooling.** If a linter, formatter, or hook enforces a rule, don't put it in CLAUDE.md. Tell Claude
   to run the tool instead.

4. **Point, don't paste.** Reference real files in the codebase rather than embedding code snippets that go stale.

5. **Alternatives, not just prohibitions.** "Use Y instead of X", never just "Don't use X" — Claude gets stuck without
   an alternative.

---

## Phase 1: Gather Evidence

Run these investigations using subagents in parallel where possible. Collect findings before writing anything.

### 1A — Project Identity

Determine:

- What is this repo? Monorepo or single project?
- What language(s) and framework(s)?
- What is the primary purpose?

```bash
# Package manager and monorepo detection
ls -la package.json pnpm-workspace.yaml lerna.json nx.json turbo.json \
      rush.json Cargo.toml pyproject.toml go.work Makefile Justfile \
      build.gradle settings.gradle 2>/dev/null

# Tech stack from lockfiles
ls -la package-lock.json pnpm-lock.yaml yarn.lock bun.lockb \
      Cargo.lock go.sum Pipfile.lock poetry.lock 2>/dev/null

# Top-level directory map
ls -d */ 2>/dev/null
```

Read the root `README.md` if it exists. Extract the one-line project description and primary tech stack.

### 1B — Build, Test, Lint Commands

These are the highest-priority entries for any CLAUDE.md.

```bash
# Package.json scripts (the single best source of truth)
cat package.json | jq '.scripts' 2>/dev/null

# Monorepo root scripts
for f in turbo.json nx.json; do
  [ -f "$f" ] && echo "=== $f ===" && cat "$f"
done

# Makefiles / Justfiles
for f in Makefile Justfile Taskfile.yml; do
  [ -f "$f" ] && echo "=== $f targets ===" && grep -E '^[a-zA-Z_-]+:' "$f"
done

# CI/CD pipeline (the REAL commands that run in production)
find .github/workflows .gitlab-ci.yml Jenkinsfile .circleci \
     -type f 2>/dev/null | head -10
```

For each CI config found, read it and extract:

- Build commands
- Test commands (including how tests are split or filtered)
- Lint/format commands
- Any commands that run on PR creation

**CI pipelines are the most trustworthy source** — they encode what actually runs, not aspirational documentation.

### 1C — Code Quality Tooling

Identify what's enforced by tools (so we DON'T put it in CLAUDE.md):

```bash
# Linting and formatting configs
ls -la .eslintrc* .prettierrc* biome.json .stylelintrc* \
       ruff.toml .flake8 .rubocop.yml .editorconfig \
       .golangci.yml clippy.toml 2>/dev/null

# Pre-commit hooks
ls -la .pre-commit-config.yaml .husky/ .git/hooks/pre-commit \
       lefthook.yml 2>/dev/null

# Type checking
ls -la tsconfig*.json mypy.ini pyrightconfig.json .mypy.ini 2>/dev/null
```

If formatters/linters exist, the CLAUDE.md should say "run the tool" not "follow these style rules."

### 1D — Directory Structure and Module Boundaries

```bash
# Top two levels of the repo (the map)
find . -maxdepth 2 -type d \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/dist/*' \
  -not -path '*/.next/*' \
  -not -path '*/build/*' \
  -not -path '*/__pycache__/*' \
  -not -name '.*' | sort

# For monorepos: identify packages/apps
find . -maxdepth 3 -name "package.json" -not -path '*/node_modules/*' \
  2>/dev/null | while read f; do
    echo "=== $f ==="
    jq '{name: .name, description: .description}' "$f" 2>/dev/null
done
```

### 1E — Existing Documentation

```bash
# Find all existing docs
find . -maxdepth 3 -name "*.md" \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -name "CHANGELOG*" | sort

# Architecture Decision Records
find . -path "*/adr/*" -o -path "*/ADR/*" -o -path "*/decisions/*" \
  2>/dev/null | head -20

# Contributing guides
find . -name "CONTRIBUTING*" -maxdepth 3 2>/dev/null
```

Read any `CONTRIBUTING.md`, `docs/architecture.md`, or ADR index to identify conventions that are already documented
somewhere.

### 1F — Git Conventions

```bash
# Commit message patterns (reveals conventions)
git log --oneline -30

# Branch naming patterns
git branch -r --sort=-committerdate | head -20

# Most active areas (what engineers actually work on)
git log --pretty=format: --name-only -200 | \
  grep -v '^$' | \
  sed 's|/[^/]*$||' | \
  sort | uniq -c | sort -rn | head -20

# Recent PR titles (reveals workflow patterns)
git log --merges --oneline -20 2>/dev/null
```

### 1G — Existing CLAUDE.md Files

```bash
# Find all existing CLAUDE.md files
find . -name "CLAUDE.md" -o -name "CLAUDE.local.md" 2>/dev/null

# Find other rule files
find . -name ".cursorrules" -o -name ".windsurfrules" \
  -o -name "copilot-instructions.md" -o -name ".github/copilot-instructions.md" \
  2>/dev/null
```

If other AI tool rulefiles exist, read them — they may contain conventions that should be in CLAUDE.md too.

---

## Phase 2: Analyze and Synthesize

Now produce your assessment. Organize findings into these buckets:

### Bucket A: Universal Commands (→ root CLAUDE.md)

Build, test, lint, typecheck commands that every engineer uses.

### Bucket B: Architecture Map (→ root CLAUDE.md)

Directory structure with one-line purpose for each major area.

### Bucket C: Conventions Claude Would Get Wrong (→ root CLAUDE.md)

Things that diverge from common open-source patterns. Examples:

- Unusual package manager choice
- Non-standard import conventions
- Custom error handling patterns
- Specific middleware ordering
- Files that must be updated together

### Bucket D: Module-Specific Knowledge (→ subdirectory CLAUDE.md)

Patterns that only apply to one package or app.

### Bucket E: Documented Elsewhere (→ pointers only)

Existing docs that CLAUDE.md should link to, not duplicate.

### Bucket F: Tool-Enforced Rules (→ hooks, NOT CLAUDE.md)

Anything a linter, formatter, or CI check already catches.

---

## Phase 3: Output

### If auditing an existing CLAUDE.md:

Produce a structured audit report:

```markdown
## CLAUDE.md Audit Report

### ✅ Correct and Valuable
[List entries that are accurate and earn their token cost]

### ❌ Should Remove
[Entries that are generic, duplicated by tooling, or that Claude
 already handles correctly without instruction. Explain why.]

### ⚠️ Should Revise
[Entries that are directionally right but too vague, too verbose,
 missing alternatives, or referencing stale paths. Show the fix.]

### ➕ Missing
[Conventions discovered in the codebase that aren't captured.
 For each, cite the evidence: which config file, which CI step,
 which code pattern proves this convention exists.]

### 📁 Should Move to Subdirectory CLAUDE.md
[Entries in the root that only apply to one area of the codebase.]

### 🔧 Should Be a Hook, Not a CLAUDE.md Rule
[Rules that should be enforced deterministically.]

### Estimated Token Cost
Current: ~[X] tokens
After proposed changes: ~[Y] tokens
```

### If building a new CLAUDE.md:

Produce the file directly, following this structure:

```markdown
# [Project Name]
[One-line description from README or package.json]

## Repository Structure
[Directory map with one-line descriptions, from Phase 1D]

## Package Manager
[From Phase 1B — only if non-obvious]

## Commands
[From Phase 1B — prioritize CI-verified commands]

## Verification
[The specific sequence to run after changes — from CI pipeline]

## Key Conventions
[ONLY items from Bucket C — things Claude would get wrong]

## Do Not
[Critical prohibitions, each with an alternative]

## Additional Context
[Pointers to docs from Bucket E]
```

Keep it under 150 lines. Ruthlessly cut anything that doesn't meet the >30% relevance threshold.

Also identify subdirectory CLAUDE.md files that should be created, and list their proposed content scope (but don't
write them yet — let the owning team handle that).

---

## Phase 4: Recommend Companion Tooling

Based on what you found, suggest:

1. **Hooks that should exist** — formatting on save, linting on edit, test gating on PR. These replace CLAUDE.md rules
   with enforcement.

2. **Skills that should exist** — multi-step workflows you discovered in the docs or CI that are too complex for a
   CLAUDE.md one-liner.

3. **Subdirectory CLAUDE.md files** — which areas of the codebase deserve their own file, and what would go in each.

---

## Interaction Style

- Ask the user BEFORE running Phase 1 whether they want an audit of an existing CLAUDE.md or a fresh build.
- Show progress as you gather evidence: "Scanning CI pipeline...", "Analyzing git conventions...", etc.
- After Phase 2, present the synthesis and ASK the user to confirm before writing any files.
- If the codebase is a monorepo, explicitly note which findings are universal vs. package-specific.
