# Universal Agent e2e specs

Playwright specs for the Universal Agent in OpenWebUI 0.11.3, plus `../agent-terminal-selector.spec.ts`. They run in the
`openwebui` project of `playwright.config.ts`, which signs into OpenWebUI directly through its OIDC login (one sign-in
per worker) instead of going through the AI-Hub portal.

No CI job runs these specs today. Run them by hand against a stack you are not sharing with someone else's manual
testing: the `@llm` specs create agent profiles and chats and spend model tokens.

## Tags

- `@ui`: structure only, no model call. Uses the existing profiles and creates nothing.
- `@llm`: drives a real Universal Agent turn. Each describe block creates its own throwaway profile (copied from an
  existing one, models pinned to `text-generation/Kimi-K2.6` and `text-generation/gemma-4-31B-it`, user memory off) in
  `beforeAll` and deletes it in `afterAll`. Retried once, since model behaviour varies.

Assertions check structure first (tool calls, sources, status lines, dialogs, file chips, all read from the chat JSON),
planted facts from `fixtures/ground_truth.json` second, and never the model's wording. Where a product decision makes
two outcomes acceptable (A2 single-row lookup, A3 administrator hint, E1 fact in the partial file), the spec records the
outcome as a test annotation instead of failing.

## Running

From `e2e/`:

```bash
# build stack (Traefik, https://openwebui.127.0.0.1.nip.io); setup creates the Keycloak e2e user
pnpm exec playwright test --project=openwebui --grep @ui
E2E_API_TOKEN=<superuser bearer token> pnpm exec playwright test --project=openwebui --grep @llm --workers=1

# dev stack (OpenWebUI on :8080, API on :8000); the setup project targets Traefik, so skip it with --no-deps
E2E_OPENWEBUI_URL=http://localhost:8080 \
E2E_API_URL=http://localhost:8000/api/v1 \
E2E_API_TOKEN=<superuser bearer token> \
E2E_OPENWEBUI_EMAIL=<existing Keycloak user> E2E_OPENWEBUI_PASSWORD=<password> \
pnpm exec playwright test --project=openwebui --no-deps --workers=1
```

| Variable                                             | Default                            | Purpose                                                    |
| ---------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------- |
| `E2E_OPENWEBUI_URL`                                  | `https://openwebui.${E2E_DOMAIN}`  | OpenWebUI base URL                                         |
| `E2E_API_URL`                                        | `https://${E2E_DOMAIN}/api/v1`     | AI-Hub API, for throwaway profiles                         |
| `E2E_TENANT`                                         | `default`                          | Tenant of the profiles                                     |
| `E2E_API_TOKEN`                                      | none; `@llm` specs skip without it | Superuser bearer token for the AI-Hub API                  |
| `E2E_OPENWEBUI_EMAIL` / `E2E_OPENWEBUI_PASSWORD`     | the `auth.setup.ts` e2e user       | Keycloak login for OpenWebUI                               |
| `E2E_UNIVERSAL_AGENT_TEMPLATE`                       | `workplace-assistant`              | Profile copied for throwaway profiles (else the first one) |
| `E2E_MAIN_LLM` / `E2E_TASK_LLM`                      | Kimi-K2.6 / gemma-4-31B-it         | Models of the throwaway profiles                           |
| `E2E_KNOWLEDGE_COLLECTION` / `_QUESTION` / `_ANSWER` | none; D1 skips without them        | Seeded collection, a question on it and the expected fact  |

The UI locators assume OpenWebUI's English interface for the e2e user, and the fixed notice in H1 is the English one.

## Preflight

Every `@llm` describe block checks its stack before the first test and fails with a message naming the cause:

- The Universal Agent class is offline: creating the profile returns 503.
- The profile never shows up in OpenWebUI within 60 s: the provisioner has not synced, or the e2e user has no access.
- The OpenWebUI functions are stale: `aihub-feature-user-files` is missing from `/api/v1/functions/` (admins) or from
  the agent model's toggle filters (everyone else).

Whether the e2e user's OpenWebUI account is linked to an AI-Hub user cannot be determined from the browser, so it is not
checked; an unlinked account shows up as the first agent turn failing.

## Fixtures

`fixtures/` holds tiny committed files with planted facts (`sales.xlsx`, `alpha.pdf`, `bravo.pdf`, the deliberately
corrupt `broken.pdf`) and `ground_truth.json`. Regenerate them with

```bash
uv run --no-project --with openpyxl --with reportlab python tests/universal-agent/fixtures/generate_fixtures.py
```

The long report for E1 (well over the 4,000-token tool-result limit) is written into the test's output directory at run
time rather than committed.

## Cases

| Case  | Spec                        | Asserts                                                                                               |
| ----- | --------------------------- | ----------------------------------------------------------------------------------------------------- |
| A1    | `integrations-menu.spec.ts` | Code Interpreter and My Files in the menu, Web Search and Image not; same in `info.meta.capabilities` |
| A2    | `withheld-tools.spec.ts`    | Code Interpreter off: no `run_command`, no sum, the toggle is named; lookup outcome annotated         |
| A3    | `withheld-tools.spec.ts`    | `read_attached_files` disabled: no read call, no source, no planted fact                              |
| B1/B2 | `tool-approval.spec.ts`     | "Agent Question" dialog per call; Confirm runs and answers, Cancel runs nothing and the chat goes on  |
| C1/C2 | `code-interpreter.spec.ts`  | `run_command` and the exact total; `display_file`, a PNG on the answer that downloads as `image/png`  |
| D1    | `knowledge.spec.ts`         | `search_knowledge` call, a knowledge source, the expected fact                                        |
| E1/E2 | `attached-files.spec.ts`    | `<name> (partial)` vs plain source names; `broken.pdf: <error>` status, the good file answers         |
| G1/G2 | `conversation.spec.ts`      | Title, `universalagent` tag, follow-ups; an edited turn branches with only the kept file              |
| G3    | `code-interpreter.spec.ts`  | Stop during `sleep 120`: no new content for 15 s, the next question is answered                       |
| H1    | `tool-call-limit.spec.ts`   | `max_tool_calls: 1`: one tool call and the fixed "I stopped looking into this" notice                 |
