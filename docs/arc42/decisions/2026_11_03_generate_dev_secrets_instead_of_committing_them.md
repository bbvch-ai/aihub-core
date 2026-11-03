# Generate Development Secrets Instead of Committing Them

## Context

`.env.dev` is the template every development `.env` starts from: `make setup`, the Claude Code web session hook, and
CI's backend tests, backup E2E test and SDK sync check all used it as is. It carried about 45 fixed secrets: database
passwords, NATS, Valkey and SeaweedFS tokens, the LiteLLM master key, the superuser token, OIDC client secrets, the
config encryption key. Some read as dev values (`admin`, `openwebui-secret-dev`), the rest were 64-character hex strings
that look like real secrets, and a secret scanner reported one of them as a leaked credential.

The values are fine on a laptop. The risk is the path from a laptop to a server: `make up-local` and `make up-build`
start a full Traefik stack from the same `.env`, and a developer who sets up staging or a customer VM that way, or copies
a working `.env` there, deploys secrets that anyone can read on GitHub. Nothing stopped that. The release bundle was
already safe, because it ships `.env.prod` as `.env.template` and `setup-env.sh` replaces its placeholders with random
values.

## Decision Drivers

- **No secret in the public repository**, so a copied file carries nothing an attacker knows.
- **One mechanism for dev and production.** `setup-env.sh` and its placeholders already exist; a second generator
  would drift from it.
- **Catch what is already out there.** The values stay in git history, so deployments made from them must be found,
  not only future ones prevented.
- **Keep regressions out**, without relying on reviewers to spot a literal secret.

## Decision

1. **`.env.dev` holds the placeholders of `.env.prod`.** Every variable `.env.prod` fills from a generated placeholder
   holds the same placeholder in `.env.dev`. A value derived from a generated one (`LITE_LLM_PROXY_API_KEY`,
   `S3_STORAGE_URL_SIGNING_SECRET`, `MONGO_CONNECTION_STRING`) references it as `'${VAR}'`.
2. **`setup-env.sh` generates every development `.env`.** `make setup`, the session hook and CI run
   `./setup-env.sh -t .env.dev -o .env`. The script also learnt to generate the Fernet key, to resolve `${VAR}`
   references after generating, to leave comments alone, and to run on BSD tools and bash 3.2.
3. **`make check-env` enforces it** (`infra/deployment/dev_env_secret_check.py`, already run by CI): a generated
   variable must hold its `.env.prod` placeholder, and any other variable named like a secret must be empty, `XXX` or a
   `${VAR}` reference.
4. **`check-env-secrets.sh` refuses published secrets.** It holds the SHA-256 of `NAME=value` for every secret
   `.env.dev` ever carried and fails on a match or on a generated placeholder left in place. The release bundle ships
   it, and `install.sh` runs it before an upgrade and stops unless `AIHUB_ALLOW_PUBLISHED_SECRETS=true`.

## Consequences

**Positive**

- A `.env` copied anywhere holds secrets unique to the checkout that generated it.
- Existing deployments built on published values are refused at their next upgrade through the installer.

**Negative**

- The dev login is no longer `admin`/`admin`; the password is `SUPERUSER_PASSWORD` in `.env`.
- A regenerated `.env` no longer matches the passwords the dev databases were created with. Developers keep their `.env`
  (and copy it to other worktrees sharing one stack) or recreate the volumes.
- Deployments not upgraded through `install.sh`, such as stacks set up from a checkout or by other tooling, are only
  protected if someone runs `check-env-secrets.sh` against their `.env`.
- The hash list does not grow by itself. It needs no update as long as `make check-env` keeps literal secrets out of
  `.env.dev`.
