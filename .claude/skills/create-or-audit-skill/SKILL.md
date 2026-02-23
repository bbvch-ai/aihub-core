---
name: create-or-audit-skill
description: >
  Builds new codebase-specific skills or reviews existing/proposed skills
  for quality, specificity, and value. Use when user says "build a skill",
  "create a skill for", "review this skill", "is this skill good", "audit
  our skills", "what skills should we have", or "clean up our skills
  directory". Also use when user says "this workflow should be a skill" or
  "help me turn this into a skill". Do NOT use for CLAUDE.md files (use
  audit-claude-md instead) or for general documentation tasks.
allowed-tools: Bash(find:*) Bash(grep:*) Bash(git:*) Bash(cat:*) Bash(head:*) Bash(wc:*) Bash(ls:*) Bash(jq:*) Read Write Edit Grep Glob
---

# Build or Review Codebase-Specific Skills

You help engineers build skills that encode THIS codebase's specific workflows, and you review contributed skills to
keep generic junk out of the skills directory.

## Core Principle: The Portability Test

A skill belongs in this repo's `.claude/skills/` ONLY if it would **fail** in a different codebase. If someone could
drop the skill into an unrelated project and it would work unchanged, it's generic and does not belong here.

Concretely, a codebase-specific skill:

- References ≥3 real file paths, commands, or patterns from THIS repo
- Encodes knowledge about THIS architecture, not general programming
- Mentions specific tools, helpers, or conventions unique to THIS team

______________________________________________________________________

## Mode 1: Build a New Skill

Trigger: User describes a workflow they want to capture.

### Step 1: Validate the Idea

Before writing anything, determine whether this SHOULD be a skill:

**Ask yourself (and the user if unclear):**

1. **Is this multi-step?** Single-step procedures belong in CLAUDE.md.
2. **Is this codebase-specific?** Generic programming workflows (writing tests, creating components, using git) don't
   need skills unless your codebase does them in a non-obvious way.
3. **Is this frequent enough?** If it happens \<1x/month, a doc pointer in CLAUDE.md is sufficient.
4. **Is it already covered?** Check existing skills and CLAUDE.md:

```bash
# List existing skills
find .claude/skills -name "SKILL.md" 2>/dev/null | while read f; do
  echo "=== $(dirname $f | xargs basename) ==="
  head -10 "$f" | grep -E '^(name|description):'
done

# Check CLAUDE.md for overlap
cat CLAUDE.md 2>/dev/null
```

5. **Should it be a hook instead?** If the rule is "always do X after Y" and X is deterministic, a PostToolUse hook is
   better.

If the answer to questions 1-3 is "no" or question 4-5 is "yes", tell the user why a skill isn't the right tool and
suggest the alternative.

### Step 2: Find the Existing Pattern

The skill should encode what senior engineers already do, not invent a new procedure. Investigate how this workflow
actually happens today:

```bash
# Find example files that follow the pattern
# (adapt these to the specific workflow)
find . -name "*.ts" -path "*/routes/*" -not -path "*/node_modules/*" \
  2>/dev/null | head -10

# Find related documentation
find . -name "*.md" -not -path "*/node_modules/*" | \
  xargs grep -li "SEARCH_TERM" 2>/dev/null | head -10

# Find recent PRs that did this workflow
git log --oneline --all -50 | grep -i "SEARCH_TERM"

# Find git commits that changed related files together
# (reveals which files are coupled in this workflow)
git log --pretty=format: --name-only -100 | \
  grep "RELEVANT_PATH" | sort | uniq -c | sort -rn | head -10
```

Read 2-3 real examples of this workflow being executed. Note:

- The exact files created or modified
- The exact commands run for verification
- The order of operations
- Any registration or wiring steps (the steps people forget)
- Edge cases or gotchas visible in code comments or PR reviews

### Step 3: Write the Skill

Use this template as a starting point. Adapt — don't follow blindly.

```yaml
---
name: {verb}-{noun}
description: >
  {What it does, referencing specific parts of THIS codebase}.
  Use when user says "{trigger phrase 1}", "{trigger phrase 2}",
  or "{trigger phrase 3}". Do NOT use for {adjacent but different
  workflow — be specific about the boundary}.
disable-model-invocation: {true if the workflow has side effects
  like creating PRs, deploying, or modifying shared config; false
  if it's safe for Claude to auto-invoke}
allowed-tools: {scope to what's needed — read-only skills should
  not have Write or Edit}
---

# {Skill Title}

## Before You Start
{Point to 1-2 real files in the codebase that exemplify the pattern.
 "Read X to see how this is done." This gives Claude concrete context.}

## Step 1: {First action}
{Concrete instruction referencing real paths and real commands.
 Not "create a file" but "create `path/to/specific/location/{name}.ts`".}

## Step 2: {Second action}
{Continue with specifics. Include the WHY if the step is non-obvious.}

...continue steps...

## Step N: Verify
{Exact commands to validate the result. Prefer a validation script
 in scripts/ over prose instructions.}

## Common Mistakes
{List 2-4 things that go wrong, drawn from real experience.
 Each mistake should reference the specific file or command involved.}
```

**Critical rules while writing:**

- **Every instruction must reference a real file path, command, or pattern from this codebase.** If you find yourself
  writing generic advice ("use descriptive names", "handle errors properly"), delete it — it's not earning its tokens.

- **The description field decides routing.** Spend extra time on it. Include 3+ trigger phrases using language engineers
  actually say. Include at least one "Do NOT use for" clause.

- **Verification is non-negotiable.** Every skill must end with a concrete verification step: a test command, a
  validation script, or a specific check. "Make sure it works" is not verification.

### Step 4: Build a Validation Script (When Appropriate)

If the workflow has a "completeness check" — did all the files get created, did the registration step happen, did the
config get updated — write a script:

```
.claude/skills/{skill-name}/
└── scripts/
    └── validate.sh
```

The script should:

- Take the key identifier as an argument (resource name, component name, etc.)
- Check each expected artifact exists
- Check each registration/wiring step was completed
- Output clear error messages for each missing piece
- Exit 0 on success, 1 on failure

Reference it in the SKILL.md's verification step.

### Step 5: Test the Skill

First, run the structural validation:

```bash
bash .claude/skills/create-or-audit-skill/scripts/validate-skill.sh .claude/skills/{skill-name}/SKILL.md
```

Fix any errors or warnings before proceeding.

Then verify semantically:

1. **Trigger test:** "When would you use the \{skill-name} skill?" — Claude should accurately describe the intended use
   case.
2. **Negative test:** Would this trigger for unrelated queries? — The description should have sufficient "Do NOT"
   scoping.
3. **File path test:** Count the real file paths referenced in the body. If fewer than 3, it's too generic.
4. **Token check:** Estimate the SKILL.md size. Flag if >500 lines.

Present the skill to the user with a summary of what it encodes and which evidence from the codebase informed each
section.

______________________________________________________________________

## Mode 2: Review an Existing Skill

Trigger: User asks to review a skill, or points to a SKILL.md file.

### The Review Protocol

Read the skill. Then run the structural check first, followed by the six semantic gates.

#### Step 0: Structural Validation

Run the bundled validation script before doing any semantic review:

```bash
bash .claude/skills/create-or-audit-skill/scripts/validate-skill.sh {path-to-SKILL.md}
```

If this fails (exit code 1), stop and report the structural errors. No point reviewing content if the skeleton is broken
— the user needs to fix naming, frontmatter, or forbidden characters first.

If it passes with warnings, note them and continue to the gates below.

#### Gate 1: The Portability Test (Hard Fail)

Read every instruction in the SKILL.md body. For each one, ask: "Does this reference something specific to THIS
codebase?"

```bash
# Count codebase-specific references
# Look for: file paths, package names, command names, function names
grep -cE '(/[a-z_-]+/|apps/|packages/|src/|pnpm |npm run |yarn )' \
  .claude/skills/{name}/SKILL.md
```

**Hard fail if:**

- The skill body contains \<3 references to real files, commands, or patterns from this codebase
- You could copy-paste the skill into a random GitHub repo and it would work identically
- The instructions are generic programming advice ("use meaningful variable names", "write clean code", "follow SOLID
  principles")

**Report:** List each instruction and classify it as CODEBASE-SPECIFIC or GENERIC. The ratio should be heavily
codebase-specific.

#### Gate 2: Overlap Check (Hard Fail)

```bash
# Check overlap with CLAUDE.md
cat CLAUDE.md 2>/dev/null

# Check overlap with other skills
find .claude/skills -name "SKILL.md" 2>/dev/null | while read f; do
  SKILL_DIR=$(dirname "$f" | xargs basename)
  echo "=== $SKILL_DIR ==="
  head -5 "$f"
  echo ""
done

# Check if a hook already handles this
cat .claude/settings.json 2>/dev/null | jq '.hooks' 2>/dev/null
```

**Hard fail if:**

- > 50% of the skill's content duplicates CLAUDE.md entries
- Another skill covers the same workflow with >70% overlap
- A hook already enforces the skill's core rule

#### Gate 3: Description Quality (Soft Fail)

Check the `description` field in frontmatter:

- [ ] Includes WHAT the skill does
- [ ] Includes ≥3 trigger phrases using natural language engineers would actually say
- [ ] Includes ≥1 "Do NOT use for" clause defining the boundary
- [ ] Under 1024 characters
- [ ] No XML angle brackets (`<` or `>`)
- [ ] Specific enough to avoid false triggers on unrelated queries

**Test it:** Ask yourself — "If a user said '{trigger phrase}', should this skill load?" and "If a user said something
adjacent but different, would this wrongly trigger?"

#### Gate 4: Instruction Quality (Soft Fail)

For each step in the skill body:

- [ ] References a real file path, command, or pattern from this repo
- [ ] Is actionable ("Create X at Y path" not "consider implementing")
- [ ] Includes the WHY when the step is non-obvious
- [ ] Does not duplicate what a linter/formatter/hook enforces

Check for common antipatterns:

- **Vague validation:** "Make sure everything works" → should be a specific test command or validation script
- **Missing registration:** The workflow creates files but doesn't mention where to register/wire them (the #1 source of
  broken skills)
- **Aspirational steps:** Instructions about what the code SHOULD do rather than what the codebase ACTUALLY does
- **Stale references:** File paths that don't exist

```bash
# Verify referenced file paths actually exist
grep -oE '["`]([a-zA-Z_./]+/[a-zA-Z_.]+)["`]' \
  .claude/skills/{name}/SKILL.md | tr -d '"`' | while read p; do
    [ ! -e "$p" ] && echo "WARNING: Referenced path does not exist: $p"
done
```

#### Gate 5: Safety and Side Effects (Soft Fail)

- [ ] `allowed-tools` scoped appropriately (review-only skills should not have Write/Edit permissions)
- [ ] No credentials, API keys, or secrets in the skill
- [ ] Validation scripts don't have destructive side effects

#### Gate 6: Token Budget (Advisory)

```bash
# Approximate token count of the skill body
wc -w .claude/skills/{name}/SKILL.md
# Rough conversion: tokens ≈ words × 1.3
```

- Under 300 lines / ~3,000 tokens: ✅ good
- 300-500 lines / ~5,000 tokens: ⚠️ consider moving details to `references/` subdirectory
- Over 500 lines: ❌ too large — will degrade performance when loaded

Also check total skill count:

```bash
find .claude/skills -name "SKILL.md" 2>/dev/null | wc -l
```

If >20 skills enabled, flag the cumulative description cost (~100 tokens per skill in the system prompt, every session).

### Review Output

Present a structured report:

```markdown
## Skill Review: {skill-name}

### Verdict: {APPROVE / REVISE / REJECT}

### Gate Results
| Gate | Result | Notes |
|------|--------|-------|
| 1. Portability Test | {PASS/FAIL} | {X/Y instructions are codebase-specific} |
| 2. Overlap Check | {PASS/FAIL} | {overlaps with X / no overlap found} |
| 3. Description Quality | {PASS/FAIL} | {specific issues} |
| 4. Instruction Quality | {PASS/FAIL} | {specific issues} |
| 5. Safety | {PASS/FAIL} | {specific issues} |
| 6. Token Budget | {OK/WARN/HIGH} | {~N tokens, N total skills} |

### Specific Issues
{For each issue, quote the problematic line and show the fix}

### Codebase Specificity Breakdown
{List each instruction, classified as CODEBASE-SPECIFIC or GENERIC}
Ratio: {X}/{Y} instructions are codebase-specific ({Z}%)

### Suggested Revisions
{Concrete rewrites, not just "make it more specific"}
```

______________________________________________________________________

## Mode 3: Audit All Skills

Trigger: User asks to audit or clean up the skills directory.

### Step 1: Inventory

```bash
echo "=== Skill Inventory ==="
find .claude/skills -name "SKILL.md" 2>/dev/null | while read f; do
  DIR=$(dirname "$f" | xargs basename)
  DESC=$(grep -A1 '^description:' "$f" | tail -1 | sed 's/^  //')
  LINES=$(wc -l < "$f")
  echo ""
  echo "Skill: $DIR"
  echo "Lines: $LINES"
  echo "Description: $DESC"
done

echo ""
echo "=== Total Skills ==="
find .claude/skills -name "SKILL.md" 2>/dev/null | wc -l
```

### Step 2: Run Structural Validation on Each Skill

Run the bundled validation script against every skill:

```bash
find .claude/skills -name "SKILL.md" | while read f; do
  echo ""
  bash .claude/skills/create-or-audit-skill/scripts/validate-skill.sh "$f"
done
```

Skills that hard-fail go directly into the "Recommend Removal or Fix" bucket. Skills that pass move on to the semantic
gates.

### Step 3: Run Portability Test and Overlap Check on Passing Skills

For each skill that passed structural validation, run Gates 1-2 from the review protocol. These are the most common
reasons skills should be removed.

### Step 4: Identify Gaps

Based on the codebase analysis (reuse techniques from audit-claude-md):

```bash
# Find documented workflows that don't have skills
find . -name "*.md" -path "*/docs/*" -not -path "*/node_modules/*" | \
  xargs grep -li "how to\|step 1\|workflow\|procedure" 2>/dev/null | head -20

# Find multi-file creation patterns (potential scaffold skills)
git log --pretty=format: --name-only -200 | \
  awk '/^$/{if(NR>1)print "---"; next}{print}' | \
  awk -F'---' '{for(i=1;i<=NF;i++) if(split($i,a,"\n")>3) print $i}' | \
  head -30
```

### Step 5: Produce Report

```markdown
## Skills Audit Report

### Summary
- Total skills: {N}
- Estimated system prompt cost: ~{N × 100} tokens per session
- Skills passing all gates: {X}/{N}

### 🗑️ Recommend Removal
{Skills that fail the Portability Test or have complete overlap}

### ✏️ Recommend Revision
{Skills with description issues, stale paths, or generic instructions}

### ✅ Healthy Skills
{Skills that pass all gates}

### 🆕 Skill Gaps
{Workflows discovered in docs/git that should be skills but aren't}

### Token Budget Assessment
Current baseline cost: ~{X} tokens from skill descriptions
Recommended target: ~{Y} tokens (after removing/consolidating)
```

______________________________________________________________________

## Interaction Style

- **Always investigate the codebase before writing.** Never generate a skill from the user's description alone — verify
  against the actual code.
- **Show your evidence.** When you reference a convention, cite the file where you found it.
- **Ask before writing files.** Present the proposed skill and get confirmation before creating it in `.claude/skills/`.
- **Be blunt about rejections.** If a proposed skill is generic, say so clearly and explain what would make it
  codebase-specific. Don't soften the feedback — generic skills actively harm performance.
- **Suggest the right tool.** If the user's need is better served by a CLAUDE.md entry, a hook, a subagent, or a doc
  pointer, say so instead of building a skill.
