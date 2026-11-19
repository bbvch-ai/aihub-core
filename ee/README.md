# bbv AI Hub Enterprise (`ee/`)

The paid agents of bbv AI Hub, built on the open Swiss AI Hub SDK:

- **Universal Agent** (`swiss_ai_hub.ee.agents.universal_agent`, image `universal_agent`)
- **Email Classification Agent** (`swiss_ai_hub.ee.agents.email_classification_agent`, image
  `email_classification_agent`)

## License

Everything in this folder is licensed under the bbv AI Hub Enterprise License in [`LICENSE`](./LICENSE), not under the
Apache-2.0 or AGPL-3.0-or-later licenses of the rest of the repository. Using it needs an agreement with bbv Software
Services and a valid bbv AI Hub Enterprise License; copying and modifying it for development and testing does not.
Contact bbv Software Services for a license.

The open core of Swiss AI Hub runs without this folder. No open package depends on `swiss-ai-hub-ee`, and the package is
never published to PyPI.

## Layout

| Path                              | Content                                                                     |
| --------------------------------- | --------------------------------------------------------------------------- |
| `swiss_ai_hub/ee/agents/`         | Agent classes, configs, events and their tests                              |
| `swiss_ai_hub/ee/i18n/`           | Translations of the enterprise agents, resolved by `EnterpriseLocaleString` |
| `app/universal_agent/`            | Entry point, templates and Dockerfile of the Universal Agent                |
| `app/email_classification_agent/` | Entry point, manual trigger, templates and Dockerfile of the Email Agent    |

The package imports the open SDK only through its public interfaces (`swiss_ai_hub.agent`,
`swiss_ai_hub.agent.capabilities`, `swiss_ai_hub.agent.imap`, `swiss_ai_hub.core.*`).

## Development

```bash
make test
make run-universal-agent
make run-email-classification-agent
```

Images are built from the repository root, for example:

```bash
docker build -f ee/app/universal_agent/Dockerfile .
```
