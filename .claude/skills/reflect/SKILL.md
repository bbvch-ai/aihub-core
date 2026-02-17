---
name: reflect
description: >-
  Reflect on the current coding session to identify where Claude needed steering, made mistakes,
  or followed suboptimal patterns. Proposes concrete improvements to CLAUDE.md files and skills
  to prevent the same issues in future sessions. Use when user says 'reflect on this session',
  'what went wrong', 'improve the prompts', 'update CLAUDE.md based on this session', 'session
  retrospective', 'what should we improve', or 'learn from mistakes'.
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Reflect - Session Retrospective & Prompt Improvement

Analyze the current session's conversation to identify mistakes, suboptimal patterns, and places where the user had to
steer or correct Claude. Propose concrete CLAUDE.md and skill improvements to prevent recurrence.

## Step 1: Analyze the Session

Review the conversation history and identify:

### Mistakes Made

- Wrong approaches that had to be corrected
- Code that didn't follow project conventions
- Incorrect assumptions about architecture or patterns

### Steering Required

- Places where the user had to redirect the approach
- Times the user said "no", "don't do that", "instead do X"
- Repeated corrections for the same issue

### Inefficiencies

- Unnecessary research that could have been avoided with better CLAUDE.md
- Missing context that caused wrong first attempts
- Patterns that should have been documented but weren't

## Step 2: Categorize Improvements

For each issue found, determine the fix category:

| Category          | When to Use                                      | Target File                           |
| ----------------- | ------------------------------------------------ | ------------------------------------- |
| **Convention**    | Claude used wrong coding pattern                 | Root `CLAUDE.md` or scope `CLAUDE.md` |
| **Architecture**  | Claude misunderstood how components connect      | Scope `CLAUDE.md`                     |
| **Skill gap**     | A skill gave wrong instructions or missed a step | `.claude/skills/*/SKILL.md`           |
| **Missing skill** | A common task has no skill                       | New skill needed                      |
| **Agent gap**     | A subagent lacks necessary context               | `.claude/agents/*.md`                 |

## Step 3: Propose Changes

For each improvement, provide:

```
### Issue: [Brief description]
**What happened**: The specific mistake or inefficiency
**Root cause**: Why the current docs/skills didn't prevent this
**Fix**: Exact change to make (file, section, new content)
**Prevention**: How this change prevents recurrence
```

## Step 4: Apply Changes (with user approval)

After presenting all proposals, ask the user which ones to apply. Then:

1. Edit the relevant CLAUDE.md, skill, or agent files
2. Verify the changes don't conflict with existing content
3. Keep changes minimal and focused — add only what's needed

## Rules

- Be honest and specific about what went wrong — vague improvements are useless
- Every proposal must include the exact file and section to change
- Prefer adding to existing sections over creating new ones
- Do not bloat CLAUDE.md with edge cases — focus on recurring patterns
- If no significant issues occurred, say so and skip the improvement phase
- Breaking changes in CLAUDE.md are fine — do not preserve backwards compatibility

## Examples

- `/reflect` — Analyze the current session and propose improvements
- Common findings:
  - "Claude kept adding try-catch blocks" → Strengthen fail-fast rule in CLAUDE.md
  - "Claude used dicts instead of Pydantic" → Add example showing the Pydantic pattern
  - "Claude didn't know about the form duality pattern" → Update agent scope CLAUDE.md
  - "The scaffold-agent skill missed the trigger step" → Fix the skill

## Troubleshooting

| Problem                                      | Solution                                                          |
| -------------------------------------------- | ----------------------------------------------------------------- |
| Session was mostly Q&A, no code              | Focus on knowledge gaps rather than coding patterns               |
| Too many issues to fix at once               | Prioritize by frequency — fix the most recurring issue first      |
| Proposed change conflicts with existing rule | Resolve the conflict explicitly — update or remove the old rule   |
| Unclear if issue is one-off or systemic      | Only add to CLAUDE.md if it would affect multiple future sessions |
