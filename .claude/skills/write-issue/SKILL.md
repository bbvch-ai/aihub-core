---
name: write-issue
description: Author a new, convention-conformant GitHub issue for bbvch-ai/aihub-core — title format, the In scope / Out of scope / Accepted when body structure, area:* and version labels, sibling and blocked-by cross-references — then create it and add it to the AI-Scrum board (org project 37) with Item Type, Priority, and Status set. Use when user says 'write an issue', 'create a GitHub issue', 'open an issue for X', 'file a bug', 'draft an epic', or 'add a story to the board'. Do NOT use for planning an existing issue's implementation (use plan-issue), breaking an issue into sub-issues (use splice-issue), or creating a PR (use create-pr).
allowed-tools: Bash, Read, Grep, Glob
---

# Write Issue — Author a Convention-Conformant GitHub Issue

Draft and create a single issue on `bbvch-ai/aihub-core`, then place it on the **AI-Scrum** board (org project 37) with
the right fields. Confirm the draft with the user **before** creating anything — issue creation and board mutation are
side effects.

## Before You Start

Read two recent issues to anchor on the house style — the body convention is the most distinctive part:

```bash
gh issue view 1452 -R bbvch-ai/aihub-core --json title,body   # Story: In/Out/Accepted-when + "Blocked by"
gh issue view 1412 -R bbvch-ai/aihub-core --json title,labels # Bug: type(scope) title + area: label
```

## Step 0: Research the Subject and Clarify

Before drafting, ground the issue in the actual codebase — an issue written from the request alone is not actionable.

1. **Research** the files, packages, conventions, and current behaviour the issue touches (grep/read the relevant code,
   docs, and config). Name real paths in the body — e.g. the relicensing surface lives in `LICENSES.md`, per-package
   `LICENSE` files, and SPDX headers, not just "the licenses".
2. **Resolve ambiguity with the user via the AskUserQuestion tool** before writing — at minimum **Item Type**
   (Epic/Story/Task) and **Priority** (P0/P1/P2), plus any scope fork the request leaves open. Never guess Priority or
   invent scope; a wrong field or an assumed boundary sends the issue back for rework.

Carry the answers into the body (Step 3) and the board fields (Step 5).

## Step 1: Decide the Item Type

Every board item is an **Epic**, **Story**, or **Task**. This drives title style, body shape, and the project field.

- **Epic** — a large theme that will hold sub-issues (e.g. #1056–#1072). Plain descriptive title, no conventional-commit
  prefix.
- **Story** — one user-facing unit of work (e.g. #1452 "Per-user overall LLM spend limits"). Plain descriptive title.
- **Task** — a technical/chore/bug unit. Title uses the `<type>(<scope>): <Subject>` form.

## Step 2: Write the Title

- **Epic / Story:** plain sentence-case description. No prefix.
  - `Per-user overall LLM spend limits`, `LLM models as an access-controlled resource`
- **Task / bug / chore:** `<type>(<scope>): <Subject starting uppercase>` — same grammar as PR titles (CI-enforced via
  `semantic-pr`).
  - Types: `fix`, `feat`, `doc`, `test`, `chore`.
  - Scopes: `swiss-ai-hub`, `iac`, `ci-cd`, `bots`, `dagster`, `deploy`, `ui`, `guards`, `rag`, `tracing`, `workflows`,
    `backup`, `sysadmin`.
  - Examples: `fix(rag): RAG agent crashes on image nodes`,
    `feat(guards): Add retry and config to context sufficient guard`,
    `chore(ci-cd): Update SonarQube Scanner action to v6`.

## Step 3: Write the Body

The standard structure (see #1452, #1451, #1449). Keep all four parts:

```markdown
{1–2 sentence context paragraph: the current state, the gap, and why it matters.
Cross-reference related issues inline with #NNN — e.g. "complementing the per-tenant
envelope from #441".}

**In scope**

- {What this issue delivers, as bullets.}

**Out of scope**

- {Explicitly excluded work, each pointing at the sibling issue that owns it — e.g.
  "Per-tenant spend limits — see #441 (sibling)."}

**Accepted when**

- [ ] {Behavior-oriented criterion — what works, not how it's built.}
- [ ] {Another criterion.}

---

**Blocked by #NNN.**   ← only if a hard dependency exists
```

Rules:

- **Accepted when** is a checkbox list (`- [ ]`) describing observable behavior. No endpoint paths, class names, or
  implementation mechanics — those change. ("Users over their hard cap are rejected at the gateway", not "add a check in
  `LiteLLMService`").

- **Out of scope** bullets name the sibling/parent issue that owns the excluded work. This is how the team keeps issues
  self-contained without scope creep.

- Use `**Blocked by #NNN.**` as a footer only for a true dependency; wire the actual relationship in Step 6.

- For a **bug**, open with current-behaviour / expected-behaviour / repro, then keep **Accepted when** as the fix
  criteria:

  ```markdown
  **Current behaviour:** {what happens today, with the error/symptom}.
  **Expected behaviour:** {what should happen}.
  **Repro:** {minimal steps, or the trigger condition}.

  **Accepted when**

  - [ ] {the bug no longer reproduces under the steps above}.
  ```

## Step 4: Create the Issue

Pick labels first:

- **area:** label(s) for every touched package — `area:api`, `area:web`, `area:agent`, `area:pipeline`, `area:process`,
  `area:bot`, `area:backup`, `area:deployment`, `area:infra`, `area:auth`, `area:github`, `area:other`. Apply all that
  fit (issues commonly carry 2–3).
- **version** label when known — exactly one of `major` / `minor` / `patch` (the PR that closes it must carry one; set
  it on the issue if it is already clear).
- Optional: `Good first issue`, `onboarding needs`, `Possible security concern`.

`gh issue create` prints the new issue URL on stdout. Capture it into `ISSUE_URL` and derive `NEW_ISSUE` (the number) —
Steps 5–7 reference both:

```bash
ISSUE_URL=$(gh issue create -R bbvch-ai/aihub-core \
  --title "feat(swiss-ai-hub): Subject here" \
  --body "$(cat <<'EOF'
Context paragraph referencing #441.

**In scope**

- ...

**Out of scope**

- ... — see #786 (sibling).

**Accepted when**

- [ ] ...

---

**Blocked by #1451.**
EOF
)" \
  --label "area:api" --label "area:auth" --label "minor")
NEW_ISSUE="${ISSUE_URL##*/}"   # the issue number, e.g. 1457
echo "Created $ISSUE_URL (#$NEW_ISSUE)"
```

## Step 5: Add to the AI-Scrum Board and Set Fields

The AI-Scrum board is **org project 37** (node id `PVT_kwDOCmtSJM4BRjLz`). Add the issue, then set the single-select
fields by option id. (Project node id and the field/option ids below verified 2026-06-10 — re-fetch if stale, see the
note at the end of this step.)

```bash
# Add the issue; capture the returned project item id.
ITEM_ID=$(gh project item-add 37 --owner bbvch-ai --url "$ISSUE_URL" --format json -q '.id')
```

Set the fields with `gh project item-edit` (project id + field id + option id):

```bash
PROJECT_ID="PVT_kwDOCmtSJM4BRjLz"

# Item Type  (field PVTSSF_lADOCmtSJM4BRjLzzhR6uAQ): Epic=6f33838e Story=38e86722 Task=f42c7a4d
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
  --field-id "PVTSSF_lADOCmtSJM4BRjLzzhR6uAQ" --single-select-option-id "38e86722"

# Status     (field PVTSSF_lADOCmtSJM4BRjLzzg_WG-g): Backlog default below; full option ids listed after this block
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
  --field-id "PVTSSF_lADOCmtSJM4BRjLzzg_WG-g" --single-select-option-id "f75ad846"

# Priority   (field PVTSSF_lADOCmtSJM4BRjLzzg_kxEg): P0=b51e3b98 P1=8d583761 P2=0f19202d
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
  --field-id "PVTSSF_lADOCmtSJM4BRjLzzg_kxEg" --single-select-option-id "8d583761"
```

Field defaults for a freshly-filed issue:

- **Status** → `Backlog` (`f75ad846`). Use `Ready` (`efca25cd`) only if the user says it is groomed and ready to pick
  up.
- **Item Type** → from Step 1.
- **Priority** → ask the user; do not guess. `P0`/`P1`/`P2`.
- **Story Points** (number field `PVTF_lADOCmtSJM4BRjLzzg_W5nk`): set only when the user gives an estimate, via
  `--field-id ... --number N`.

Full Status option ids: `Stateless`=9b2296d7, `Backlog`=f75ad846, `Ready`=efca25cd, `Current Sprint`=0141227c,
`In Progress`=47fc9ee4, `Dev Done`=e27f8bc6, `Done`=98236657, `Completed`=026feb3e, `Aborted`=0cbe70c4.

> If `gh project` reports a stale field/option id, re-fetch with
> `gh project field-list 37 --owner bbvch-ai --format json` and use the current ids.

## Step 6: Wire Relationships (if any)

- **Parent ↔ child (Epic holds Stories/Tasks):** use `addSubIssue` (see `.claude/skills/splice-issue/SKILL.md` for the
  full pattern).
- **Hard dependency (matches the `**Blocked by #NNN.**` footer):** use `addBlockedBy`.

```bash
ISSUE_ID=$(gh api graphql -F number=$NEW_ISSUE -f query='
  query($number: Int!) { repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $number) { id } } }' \
  -q '.data.repository.issue.id')
BLOCKING_ID=$(gh api graphql -F number=$BLOCKING_ISSUE -f query='
  query($number: Int!) { repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $number) { id } } }' \
  -q '.data.repository.issue.id')
gh api graphql -f query="mutation { addBlockedBy(input: { issueId: \"$ISSUE_ID\", blockingIssueId: \"$BLOCKING_ID\" }) { issue { id } } }"
```

`addSubIssue` = "part of this work"; `addBlockedBy` = "must be done first". Never use one for the other.

## Step 7: Verify

```bash
bash .claude/skills/write-issue/scripts/validate-issue.sh "$NEW_ISSUE"
```

The script confirms the issue exists, carries at least one `area:*` label, has the `In scope` / `Out of scope` /
`Accepted when` sections (skip for pure bugs if the user opted out), and is on the AI-Scrum board with an Item Type set.
Report any gap and fix it before declaring done.

## Common Mistakes

1. **Conventional-commit prefix on an Epic/Story.** Only Tasks/bugs use `type(scope):`. Epics and Stories get plain
   descriptive titles (#1452, #1449).
2. **Implementation detail in Accepted when.** Criteria describe behavior, not class names or endpoint paths — those
   churn and rot the issue. Put mechanics in the context paragraph.
3. **Out of scope without a pointer.** Every excluded item names the sibling/parent issue that owns it (`— see #786`). A
   bare "out of scope" bullet invites scope creep back in.
4. **Forgetting the board.** An issue not added to org project 37 is invisible to the sprint — Step 5 is not optional.
   Item Type is mandatory; Status defaults to `Backlog`.
5. **Guessing Priority.** P0/P1/P2 is a product call — ask, don't assume.
