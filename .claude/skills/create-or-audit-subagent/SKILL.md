---
name: create-or-audit-subagent
description: >
  Builds new codebase-specific subagents or reviews existing/proposed
  subagents for quality, specificity, and proper scoping. Use when user
  says "build a subagent", "create an agent", "review this agent",
  "audit our agents", "clean up agents directory", or "what agents
  should we have". Also use when user says "I need a specialized agent
  for" or "make an agent that". Do NOT use for skills (use audit-skill),
  CLAUDE.md files (use audit-claude-md), or for agent teams.
allowed-tools: Bash(find:*) Bash(grep:*) Bash(git:*) Bash(cat:*) Bash(head:*) Bash(wc:*) Bash(ls:*) Bash(jq:*) Read Write Edit Grep Glob
---

# Build or Review Codebase-Specific Subagents

You help engineers build subagents that solve real problems in THIS codebase, and you review contributed subagents to
prevent the directory from filling up with generic agents that add overhead without value.

## How Subagents Differ from Skills

Understand this before building anything:

| Dimension        | Skill                                        | Subagent                                                                                   |
| ---------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Runs where       | Main conversation context                    | Isolated context window                                                                    |
| Body is          | Workflow instructions Claude follows         | System prompt for a separate agent                                                         |
| Best for         | Multi-step procedures with specific ordering | Tasks that produce heavy output, need tool restrictions, or benefit from a focused persona |
| Context impact   | Loaded into main window (costs tokens there) | Runs separately, returns only a summary                                                    |
| Can modify files | Yes (in main context)                        | Yes (in its own context, with its own tool access)                                         |
| Persistence      | None across sessions                         | Optional memory via `memory` field                                                         |

**The key decision:** If the workflow runs best as step-by-step instructions in the main conversation, make it a skill.
If it runs best as an isolated agent with its own context, restricted tools, and a focused persona that returns a
summary, make it a subagent.

## Core Principle: The Specificity Test

A subagent belongs in `.claude/agents/` ONLY if its system prompt encodes knowledge specific to THIS codebase. A generic
"code reviewer" or "debugger" adds nothing — Claude already knows how to review code and debug. Your subagent should
know how to review code *in this specific codebase* and debug *this specific architecture*.

Concretely, a codebase-specific subagent:

- References real file paths, helper functions, or patterns from this repo
- Knows about this project's architecture, not just general programming
- Has tool restrictions that match what it actually needs in THIS codebase
- Preloads project-specific skills when relevant
- Has a description that references this project's domain

______________________________________________________________________

## Mode 1: Build a New Subagent

Trigger: User describes a need for a specialized agent.

### Step 1: Validate the Idea

Before writing anything, determine whether this SHOULD be a subagent:

**Ask yourself (and the user if unclear):**

1. **Does it need an isolated context?** If the task produces heavy output (test results, large code scans,
   documentation analysis) that would pollute the main conversation — subagent. If it's a sequence of steps the user
   wants to watch — skill.

2. **Does it need restricted tools?** If the agent should be read-only, or should only run specific commands — subagent.
   If it needs the same tools as a normal session — probably a skill or CLAUDE.md.

3. **Does it benefit from a persistent persona?** If the agent builds knowledge over time (via `memory`) about this
   codebase's patterns, recurring issues, or architectural decisions — subagent.

4. **Is it already covered?**

```bash
# List existing subagents
find .claude/agents -name "*.md" 2>/dev/null | while read f; do
  echo "=== $(basename "$f" .md) ==="
  head -15 "$f" | grep -E '^(name|description|tools|model):'
done

# Check built-in agents (Explore, Plan, general-purpose already exist)
echo ""
echo "Built-in agents: Explore (read-only search), Plan (research for planning), general-purpose (all tools)"
```

5. **Would a skill be better?** If the user wants a multi-step workflow with explicit ordering and verification gates,
   that's a skill. If they want an isolated agent with a focused persona and restricted capabilities, that's a subagent.

If a subagent isn't the right tool, say so and redirect.

### Step 2: Investigate the Codebase

The subagent's system prompt should be grounded in what actually exists. Investigate the area the subagent will operate
in:

```bash
# Understand the area the subagent will work with
# (adapt these to the specific domain)

# Find relevant files and patterns
find . -name "*.ts" -path "*/{relevant_area}/*" \
  -not -path "*/node_modules/*" 2>/dev/null | head -20

# Find existing test patterns (for test-runner agents)
find . -name "*.test.*" -not -path "*/node_modules/*" | head -10

# Find project-specific commands
cat package.json 2>/dev/null | jq '.scripts' 2>/dev/null

# Find existing skills the subagent could preload
find .claude/skills -name "SKILL.md" 2>/dev/null | while read f; do
  DIR=$(dirname "$f" | xargs basename)
  DESC=$(grep -A1 '^description:' "$f" | tail -1 | sed 's/^  //')
  echo "$DIR: $DESC"
done

# Find existing documentation the subagent should know about
find . -maxdepth 3 -name "*.md" -path "*/docs/*" \
  -not -path "*/node_modules/*" 2>/dev/null | head -15
```

Read 2-3 files that represent the patterns the subagent will encounter. The system prompt should teach the subagent
about THESE specific patterns, not generic programming concepts.

### Step 3: Determine Configuration

Before writing the file, decide each configuration field:

**model** — Match the model to the task complexity:

- `haiku`: Fast, cheap. Good for: file scanning, grep-heavy exploration, simple validation, high-volume operations where
  speed matters. Only use this model for trivial tasks.
- `sonnet` or `inherit`: Balanced. Good for: code review, refactoring analysis, debugging, most simple work.
- `opus`: Maximum reasoning. Good for: architecture decisions, complex multi-step debugging, security analysis, coding.
  Use for most tasks like coding, reasoning or complex decision making.

**tools** — Principle of least privilege. Start with the minimum:

- Read-only agents: `Read, Grep, Glob` (add `Bash` only if they need to run read-only commands like `git log` or
  `pnpm typecheck`)
- Agents that fix things: `Read, Edit, Write, Bash, Grep, Glob`
- Never give Write/Edit to agents that should only analyze

**disallowedTools** — Use this instead of `tools` when you want to inherit everything EXCEPT a few specific tools:

- Review agents: `disallowedTools: Write, Edit`
- Safe exploration: `disallowedTools: Write, Edit, Bash`

**permissionMode** — Match the risk level:

- `default`: Agent asks permission for risky ops. Use for most agents.
- `acceptEdits`: Auto-accepts file edits. Use for trusted fix-it agents.
- `plan`: Read-only exploration. Use for research/analysis agents.
- `bypassPermissions`: Use only in sandboxed/CI environments.

**memory** — Enable only when the agent genuinely accumulates knowledge:

- `project`: Knowledge specific to this codebase, shareable via git. Good for: codebase explorers, pattern trackers,
  review agents that learn recurring issues.
- `user`: Knowledge that spans projects. Good for: personal preference agents, cross-project pattern agents.
- `local`: Project-specific but personal. Good for: debugging notes, local environment quirks.
- Omit if the agent does a self-contained task each time.

**skills** — Preload project-specific skills that give the subagent domain knowledge it would otherwise need to
discover:

```yaml
skills:
  - multi-tenant-context    # if it touches tenant-scoped code
  - api-conventions          # if it works on API endpoints
```

Only preload skills that are relevant to every invocation of this subagent. Each preloaded skill consumes context.

**hooks** — Add when you need deterministic guardrails:

- PreToolUse on Bash: validate commands before execution
- PostToolUse on Edit/Write: run linter/formatter after changes
- Stop: cleanup or notification when agent finishes

**maxTurns** — Set a ceiling to prevent runaway agents:

- Quick lookup agents: 10-15
- Review agents: 20-30
- Complex debugging: 40-50
- Omit for no limit (use with caution)

### Step 4: Write the Subagent

Use this template. The body is a SYSTEM PROMPT, not workflow instructions — write it as directives to the agent, not
steps for a user.

```markdown
---
name: {role}-{scope}
description: >
  {What it does in THIS codebase}. Use when {trigger phrases using
  language engineers actually say}. Use proactively {if it should
  auto-trigger after related actions}. Do NOT use for {boundary}.
tools: {minimum required tools}
model: {appropriate model}
permissionMode: {appropriate mode}
memory: {scope, or omit}
skills:
  - {relevant-project-skill}
maxTurns: {ceiling}
---

You are a {role} for {this specific project/codebase}.

## What You Know About This Codebase

{2-5 bullet points about the specific architecture, patterns, and
conventions this agent needs to know. Reference real file paths.}

## When Invoked

{What the agent should do first — typically orient itself by reading
specific files or running specific commands.}

## How to {Do the Thing}

{Domain-specific instructions grounded in THIS codebase. Reference
real file paths, real function names, real commands.}

## What to Report Back

{Specify the output format so the summary returned to the main
conversation is concise and useful.}
```

**Critical rules while writing the system prompt:**

- **Ground every instruction in this codebase.** Not "look for security issues" but "check for missing tenant_id filters
  (see `packages/db/src/middleware/tenant.ts` for the expected pattern)."

- **Tell it what to read first.** Subagents start with zero context about the codebase. The system prompt should point
  them to the most important files for orientation.

- **Specify the output format.** The summary returned to the main conversation should be structured and concise — the
  whole point of a subagent is to keep detail out of the main context.

- **Don't duplicate the system prompt.** Subagents do NOT receive Claude Code's full system prompt. They get their own
  system prompt (the body), basic environment info (cwd, OS), and preloaded skills. Include everything the agent needs
  to know.

### Step 5: Validate

Run the structural validation:

```bash
bash .claude/skills/create-or-audit-subagent/scripts/validate-subagent.sh \
  .claude/agents/{name}.md
```

Then verify semantically:

1. **Trigger test:** "When would you use the \{name} subagent?" — Claude should accurately describe the intended use
   case.
2. **Tool scope test:** Does the agent have the MINIMUM tools needed? Could any be removed?
3. **Specificity test:** Count codebase-specific references in the system prompt. If fewer than 3, it's too generic.
4. **Context cost test:** If skills are preloaded, estimate total token cost. Flag if the subagent starts with >5,000
   tokens of preloaded context.

Present the subagent to the user with a summary of configuration choices and which evidence from the codebase informed
the system prompt.

______________________________________________________________________

## Mode 2: Review an Existing Subagent

Trigger: User asks to review a subagent, or points to an agent file.

### Step 0: Structural Validation

Run the bundled validation script:

```bash
bash .claude/skills/create-or-audit-subagent/scripts/validate-subagent.sh {path}
```

If this fails (exit code 1), stop and report structural errors. Fix the skeleton before reviewing content.

### Gate 1: The Specificity Test (Hard Fail)

Read the system prompt body. For each instruction, ask: "Does this reference something specific to THIS codebase?"

```bash
# Count codebase-specific references in the system prompt
grep -cE '(`[a-zA-Z_./]+/[a-zA-Z_.]+`|apps/|packages/|src/|scripts/)' \
  .claude/agents/{name}.md 2>/dev/null
```

**Hard fail if:**

- The system prompt contains \<3 references to real files, commands, or patterns from this codebase
- The agent is a generic "code reviewer" or "debugger" with no project-specific knowledge
- You could drop this agent into a different repo unchanged

**Report:** Classify each instruction as CODEBASE-SPECIFIC or GENERIC.

### Gate 2: Overlap Check (Hard Fail)

```bash
# Check overlap with built-in agents
echo "Built-in: Explore (read-only search), Plan (planning research), general-purpose (all tools)"

# Check overlap with other custom agents
find .claude/agents -name "*.md" 2>/dev/null | while read f; do
  NAME=$(basename "$f" .md)
  echo "=== $NAME ==="
  head -5 "$f"
  echo ""
done

# Check if a skill already covers this workflow
find .claude/skills -name "SKILL.md" 2>/dev/null | while read f; do
  DIR=$(dirname "$f" | xargs basename)
  DESC=$(grep -A1 '^description:' "$f" | tail -1 | sed 's/^  //')
  echo "$DIR: $DESC"
done
```

**Hard fail if:**

- The subagent duplicates a built-in agent's purpose (especially Explore — many custom "codebase explorer" agents are
  redundant)
- Another custom subagent covers the same domain with >70% overlap
- A skill already handles this workflow (and doesn't need isolation)

### Gate 3: Tool Scoping (Soft Fail)

Review the `tools` or `disallowedTools` field:

- [ ] Agent has the MINIMUM tools needed for its purpose
- [ ] Read-only agents do NOT have Write or Edit
- [ ] Agents that shouldn't run arbitrary commands don't have Bash (or have PreToolUse hooks validating Bash commands)
- [ ] If `permissionMode: bypassPermissions`, there's a strong justification (CI/sandbox only)
- [ ] If no `tools` field is set, the agent inherits ALL tools — is this intentional?

Common red flags:

- A "reviewer" agent with Write/Edit permissions
- An "explorer" agent with Bash but no command validation
- `bypassPermissions` on an agent that modifies files

### Gate 4: Description Quality (Soft Fail)

The description determines when Claude auto-delegates:

- [ ] Describes what the agent does in THIS codebase (not generically)
- [ ] Includes trigger phrases engineers would naturally say
- [ ] Includes "Use proactively" if it should auto-trigger after related actions (e.g., "use proactively after code
  changes")
- [ ] Includes scope boundary ("Do NOT use for...")
- [ ] Under ~200 characters for efficient routing

### Gate 5: System Prompt Quality (Soft Fail)

- [ ] Tells the agent what to read first (orientation step)
- [ ] References real file paths and patterns from this codebase
- [ ] Specifies the output format for the summary
- [ ] Doesn't duplicate generic knowledge Claude already has
- [ ] Doesn't try to replicate CLAUDE.md (subagents don't see it)
- [ ] Includes project-specific knowledge the agent needs (subagents only get their own system prompt, not the full
  Claude Code system prompt)

Check for common antipatterns:

- **Missing orientation:** System prompt doesn't tell the agent where to look first → agent wastes turns exploring
- **Over-broad persona:** "You are an expert in everything" → provides no focus
- **Duplicating Claude's knowledge:** Instructions like "write clean code" or "use meaningful variable names" → waste
  tokens
- **No output format:** Agent returns unstructured results → pollutes main conversation context

### Gate 6: Configuration Hygiene (Soft Fail)

- [ ] `model` matches task complexity (sonnet for fast scans, not opus)
- [ ] `memory` is enabled only if the agent genuinely accumulates knowledge across sessions
- [ ] `maxTurns` is set to prevent runaway execution
- [ ] Preloaded `skills` are all relevant to every invocation (not "nice to have" skills that waste context)
- [ ] `hooks` are defined for any operations that need guardrails
- [ ] `mcpServers` are scoped to what the agent actually needs

### Gate 7: Token Budget (Advisory)

```bash
# Approximate the subagent's startup cost
BODY_WORDS=$(wc -w < ".claude/agents/{name}.md")
echo "System prompt: ~$BODY_WORDS words (~$(( BODY_WORDS * 13 / 10 )) tokens)"

# Check preloaded skills
grep -A5 '^skills:' ".claude/agents/{name}.md" 2>/dev/null
```

If skills are preloaded, estimate their combined size:

```bash
grep -A10 '^skills:' ".claude/agents/{name}.md" | \
  grep '^ *-' | sed 's/^ *- *//' | while read skill; do
    SKILL_FILE=".claude/skills/${skill}/SKILL.md"
    if [ -f "$SKILL_FILE" ]; then
      WORDS=$(wc -w < "$SKILL_FILE")
      echo "  $skill: ~$WORDS words (~$(( WORDS * 13 / 10 )) tokens)"
    fi
done
```

A subagent's effective context budget = 200k minus system prompt minus preloaded skills. If startup cost exceeds 10k
tokens, flag it.

### Review Output

```markdown
## Subagent Review: {name}

### Verdict: {APPROVE / REVISE / REJECT}

### Gate Results
| Gate | Result | Notes |
|------|--------|-------|
| 1. Specificity Test | {PASS/FAIL} | {X/Y instructions are codebase-specific} |
| 2. Overlap Check | {PASS/FAIL} | {overlaps with X / no overlap} |
| 3. Tool Scoping | {PASS/FAIL} | {appropriate / over-permissive / missing restriction} |
| 4. Description Quality | {PASS/FAIL} | {specific issues} |
| 5. System Prompt Quality | {PASS/FAIL} | {specific issues} |
| 6. Configuration Hygiene | {PASS/FAIL} | {specific issues} |
| 7. Token Budget | {OK/WARN/HIGH} | {~N tokens startup cost} |

### Specificity Breakdown
{List each instruction, classified as CODEBASE-SPECIFIC or GENERIC}
Ratio: {X}/{Y} instructions are codebase-specific ({Z}%)

### Configuration Assessment
- Model: {appropriate / over-powered / under-powered}
- Tools: {minimal / over-permissive — list unnecessary tools}
- Memory: {appropriate / unnecessary / missing}
- Permissions: {appropriate / too loose}

### Suggested Revisions
{Concrete rewrites for system prompt, description, and config}
```

______________________________________________________________________

## Mode 3: Audit All Subagents

Trigger: User asks to audit or clean up the agents directory.

### Step 1: Inventory

```bash
echo "=== Custom Subagents ==="
find .claude/agents -name "*.md" 2>/dev/null | while read f; do
  NAME=$(basename "$f" .md)
  MODEL=$(grep '^model:' "$f" | sed 's/model: *//')
  TOOLS=$(grep '^tools:' "$f" | sed 's/tools: *//')
  MEMORY=$(grep '^memory:' "$f" | sed 's/memory: *//')
  LINES=$(wc -l < "$f")
  echo ""
  echo "Agent: $NAME"
  echo "  Model: ${MODEL:-inherit}"
  echo "  Tools: ${TOOLS:-all (inherited)}"
  echo "  Memory: ${MEMORY:-none}"
  echo "  Lines: $LINES"
  DESC=$(grep -A2 '^description:' "$f" | tail -2 | sed 's/^  //' | tr '\n' ' ')
  echo "  Description: $DESC"
done

echo ""
echo "=== User-Level Subagents ==="
find ~/.claude/agents -name "*.md" 2>/dev/null | while read f; do
  echo "  $(basename "$f" .md)"
done

echo ""
TOTAL=$(find .claude/agents -name "*.md" 2>/dev/null | wc -l)
echo "Total project-level subagents: $TOTAL"
```

### Step 2: Structural Validation

Run the validation script against every subagent:

```bash
find .claude/agents -name "*.md" 2>/dev/null | while read f; do
  echo ""
  bash .claude/skills/create-or-audit-subagent/scripts/validate-subagent.sh "$f"
done
```

### Step 3: Check for Redundancy with Built-ins

The most common problem: custom agents that duplicate built-in capabilities.

```bash
find .claude/agents -name "*.md" 2>/dev/null | while read f; do
  NAME=$(basename "$f" .md)
  BODY=$(tail -n +$(awk '/^---$/{n++; if(n==2){print NR; exit}}' "$f") "$f")

  # Check if it's basically Explore
  if echo "$BODY" | grep -qiE '(search|scan|find|explore|discover).*codebase' && \
     ! grep -q 'Write\|Edit' "$f"; then
    echo "WARNING: $NAME may overlap with built-in Explore agent"
  fi

  # Check if it's basically Plan
  if echo "$BODY" | grep -qiE '(plan|architect|design|research)' && \
     grep -q 'plan' "$f"; then
    echo "WARNING: $NAME may overlap with built-in Plan agent"
  fi
done
```

### Step 4: Specificity Sweep

For each subagent, count codebase-specific references:

```bash
find .claude/agents -name "*.md" 2>/dev/null | while read f; do
  NAME=$(basename "$f" .md)
  REFS=$(grep -cE '(`[a-zA-Z_./]+/[a-zA-Z_.]+`|apps/|packages/|src/|scripts/)' "$f" 2>/dev/null || echo 0)
  echo "$NAME: $REFS codebase-specific references"
  if [ "$REFS" -lt 3 ]; then
    echo "  ⚠️  May be too generic"
  fi
done
```

### Step 5: Identify Gaps

Based on the codebase, are there subagent opportunities being missed?

```bash
# High-output operations that would benefit from isolation
echo "=== Potential Subagent Opportunities ==="

# Test suites (heavy output → good subagent candidate)
TEST_FILES=$(find . -name "*.test.*" -not -path "*/node_modules/*" 2>/dev/null | wc -l)
echo "Test files: $TEST_FILES (test-runner subagent?)"

# Documentation volume
DOC_FILES=$(find . -name "*.md" -path "*/docs/*" -not -path "*/node_modules/*" 2>/dev/null | wc -l)
echo "Doc files: $DOC_FILES (doc-researcher subagent?)"

# Database/migration files
MIGRATION_FILES=$(find . -name "*migration*" -o -name "*migrate*" 2>/dev/null | wc -l)
echo "Migration files: $MIGRATION_FILES (db-analyst subagent?)"

# API endpoint count
API_FILES=$(find . -name "*.ts" -path "*/routes/*" -not -path "*/node_modules/*" 2>/dev/null | wc -l)
echo "Route files: $API_FILES (api-reviewer subagent?)"
```

### Step 6: Produce Report

```markdown
## Subagent Audit Report

### Summary
- Project-level subagents: {N}
- User-level subagents: {N}
- Passing all gates: {X}/{N}

### 🗑️ Recommend Removal
{Subagents that fail Specificity Test, duplicate built-ins, or have
complete overlap with other agents or skills}

### ✏️ Recommend Revision
{Subagents with over-permissive tools, weak descriptions, generic
system prompts, or missing configuration}

### ✅ Healthy Subagents
{Subagents that pass all gates}

### 🆕 Subagent Gaps
{Operations in this codebase that produce heavy output, need tool
restrictions, or benefit from persistent memory — and don't have
subagents yet}

### ⚖️ Should Be Skills Instead
{Subagents that are really workflow instructions, not isolated
agents — better served as skills in the main conversation}

### Configuration Summary
| Agent | Model | Tools | Memory | Turns | Verdict |
|-------|-------|-------|--------|-------|---------|
{table of all agents with configuration and verdict}
```

______________________________________________________________________

## Interaction Style

- **Always investigate the codebase before writing.** Never generate a subagent from the user's description alone.
- **Challenge "code reviewer" and "debugger" requests.** These are the most commonly over-built subagents. Ask: "What
  does reviewing code in THIS codebase specifically require that Claude doesn't already do?" If the answer is "nothing
  special," suggest they skip the agent.
- **Push for minimal tools.** Default to read-only. Make the user justify every write/edit permission.
- **Check against built-ins.** Before building any exploration or analysis agent, compare it to Explore. Before building
  any planning agent, compare it to Plan. The bar for custom agents that overlap built-ins is high.
- **Be blunt about rejections.** Generic subagents consume the description routing budget and confuse Claude's
  delegation logic. Fewer, sharper agents outperform many vague ones.
- **Suggest the right tool.** If a skill, hook, or CLAUDE.md entry would serve better, redirect.
