# ee - bbv AI Hub Enterprise (bbv AI Hub Enterprise License)

**Purpose**: The paid agents of bbv AI Hub — the Universal Agent and the Email Classification Agent — built on the open
agent SDK in `packages/agent`.

**License**: bbv AI Hub Enterprise License (`ee/LICENSE`), not Apache-2.0 or AGPL. Using the code needs an agreement
with bbv Software Services; development and testing do not. The package is never published to PyPI
(`Private :: Do Not Upload`).

## Boundary rules

- Dependencies point one way: `ee` → `packages/agent` → `packages/core`. No open package may import `swiss_ai_hub.ee`.
- Import the open SDK only through its public interfaces: `swiss_ai_hub.agent`, `swiss_ai_hub.agent.capabilities`,
  `swiss_ai_hub.agent.imap`, `swiss_ai_hub.agent.agents`, `swiss_ai_hub.core.*`. A name missing there is added to that
  `__init__.py` in `packages/agent`, not imported by its deep module path. Test doubles from the open package's `tests/`
  modules are the exception.
- Agent class names, agent types and event names must not change: saved profiles, chats, mailboxes and event history
  refer to them by name.
- Strings use `EnterpriseLocaleString` (`swiss_ai_hub/ee/i18n/`), which resolves the shared `agent.*` translations plus
  the ones in `swiss_ai_hub/ee/i18n/translations/agent/`.

## Layout

```
ee/
├── LICENSE                           # bbv AI Hub Enterprise License
├── swiss_ai_hub/ee/
│   ├── agents/
│   │   ├── universal_agent/          # Model picks its own tools (knowledge, files, memory, sandbox)
│   │   ├── email_classification_agent/ # Non-conversational: files unread mail into category folders
│   │   └── tests/                    # Blueprint rules the open package checks for its own agents
│   └── i18n/                         # EnterpriseLocaleHandler / EnterpriseLocaleString + translations
└── app/                              # Entry points, templates and Dockerfiles (built from the repo root)
    ├── universal_agent/
    └── email_classification_agent/
```

The agent architecture, capabilities and workflow rules are documented in `packages/agent/CLAUDE.md`; they apply here
unchanged.

## Commands

| Command                               | What it does              |
| ------------------------------------- | ------------------------- |
| `make test`                           | Run the ee test suite     |
| `make run-universal-agent`            | Start the Universal Agent |
| `make run-email-classification-agent` | Start the Email Agent     |
