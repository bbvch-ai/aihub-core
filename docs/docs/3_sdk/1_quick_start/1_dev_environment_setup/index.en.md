---
title: Development Environment Setup
---

# Development environment setup

This page takes you from a clean Windows machine to a running Swiss AI Hub development stack. The infrastructure
(databases, NATS, Keycloak, LiteLLM, Milvus, SeaweedFS, Langfuse and friends) runs in Docker; the code you actually work
on runs from your checkout on the host with hot reload. You edit a Python file and the API restarts, you edit a Vue
component and the browser updates, and nothing gets rebuilt into an image.

The reference environment is Ubuntu on WSL2 with Docker Desktop, because that is what most of the team develops on.
Everything from [Install the toolchain](#step-3-install-the-toolchain) onwards is plain Linux and works identically on a
native Ubuntu box or on macOS.

## Step 1: Install Ubuntu on WSL2

Open PowerShell as Administrator and install a distribution:

```powershell
wsl --install -d Ubuntu-24.04
```

Reboot if prompted, then set your Linux username and password when the Ubuntu console opens. Confirm you are on WSL
version 2:

```powershell
wsl --list --verbose
```

The `VERSION` column must read `2`. WSL 1 cannot run Docker Desktop's engine integration.

::: warning Keep the repository in the Linux filesystem
Clone into your Linux home directory (`~/projects/aihub-core`), never into a Windows path mounted under `/mnt/c`.
Cross-filesystem I/O through `/mnt` is roughly an order of magnitude slower, and inotify events do not propagate, so
`uv sync` crawls and hot reload silently stops working for both the API and the admin UI.
:::

WSL takes half of your host RAM by default, which is not enough for a stack that wants 32 GB. Create
`C:\Users\<you>\.wslconfig` on the Windows side:

```ini
[wsl2]
memory=32GB
processors=8
swap=16GB
```

Apply it with `wsl --shutdown` in PowerShell, then reopen Ubuntu.

## Step 2: Enable the WSL backend in Docker Desktop

Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/), then open its settings:

1. **General** — tick *Use the WSL 2 based engine*.
2. **Resources → WSL integration** — tick *Enable integration with my default WSL distro*, or enable your Ubuntu
   distribution explicitly in the list below it.
3. **Resources → Network** — tick *Enable host networking*.

The third one is not optional. The `open-webui` container runs with `network_mode: host` so that it can reach the API
and the OTEL collector on localhost. Without host networking enabled, that container fails to bind and the chat UI on
port 8080 never comes up, while every other service looks healthy.

Verify from inside the Ubuntu shell, not from PowerShell:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

If `docker` is not found in Ubuntu, the WSL integration toggle did not take; restart Docker Desktop and check the distro
is listed.

## Step 3: Install the toolchain

Everything below runs inside Ubuntu.

```bash
sudo apt update
sudo apt install -y build-essential git curl make
```

Install [uv](https://docs.astral.sh/uv/), which manages both the virtual environment and the Python 3.13 interpreter the
workspace pins:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

Install Node.js 22 or newer and enable pnpm through corepack. The frontends and the documentation site need it; the
Python packages do not.

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
source ~/.bashrc
nvm install 22
corepack enable
```

Check the result:

```bash
uv --version
node --version     # v22.x or newer
pnpm --version     # 10.x
make --version
docker compose version
```

You do not need to install Python yourself. `uv sync` downloads the interpreter that `requires-python = ">=3.13, <3.14"`
asks for.

## Step 4: Clone and bootstrap

```bash
git clone https://github.com/bbvch-ai/aihub-core.git ~/projects/aihub-core
cd ~/projects/aihub-core
make setup-all
```

`make setup-all` runs two things: `make setup` resolves every workspace package with `uv sync --all-packages` and copies
`.env.dev` to `.env` if you do not already have one, and `make setup-frontend` installs the frontend dependencies with
pnpm. Run them separately if you only want one half.

The generated `.env` is a complete, working development configuration. Every secret in it is a known dev value, and the
Swiss LLM Cloud endpoints are the only entries you may want to fill in for real model access.

::: danger Development credentials only
`.env.dev` contains hard-coded passwords, signing keys and API tokens that are public in the repository, including
`SUPERUSER_PASSWORD='admin'`. It is fine on your machine and unusable anywhere else. Never copy it to a shared or
internet-facing host.
:::

## Step 5: Start the infrastructure

```bash
make up-dev
```

This is `docker compose -f infra/docker-compose.dev.yml --env-file .env up -d --build` and starts around 30 containers.
The first run pulls several gigabytes of images and takes a while; Milvus, Keycloak and Langfuse need another minute or
two after that to report healthy.

Watch it settle:

```bash
docker compose -f infra/docker-compose.dev.yml ps
docker compose -f infra/docker-compose.dev.yml logs -f keycloak
```

Once everything is up, these are published on localhost:

| Service    | URL / port                                     | What it is                      |
| ---------- | ---------------------------------------------- | ------------------------------- |
| OpenWebUI  | [http://localhost:8080](http://localhost:8080) | Chat interface                  |
| Keycloak   | [http://localhost:8180](http://localhost:8180) | Identity provider (realm aihub) |
| Langfuse   | [http://localhost:6006](http://localhost:6006) | LLM tracing and cost tracking   |
| Attu       | [http://localhost:3003](http://localhost:3003) | Milvus admin UI                 |
| SeaweedFS  | [http://localhost:8889](http://localhost:8889) | Filer UI (S3 gateway on 9000)   |
| LiteLLM    | `localhost:4000`                               | LLM gateway                     |
| NATS       | `localhost:4222`                               | Event backbone                  |
| Milvus     | `localhost:19530`                              | Vector database                 |
| FerretDB   | `localhost:27017`                              | Document storage                |
| PostgreSQL | `localhost:5432`                               | Relational storage              |
| Valkey     | `localhost:6379`                               | Agent state                     |
| Neo4j      | [http://localhost:7474](http://localhost:7474) | Graph memory                    |
| MinerU     | `localhost:8002`                               | Document parsing                |

Stop it again with `make down-dev` when you are done for the day.

## Step 6: Run only the processes you need

The containers above cover the infrastructure. Which application processes you start on top depends on what you are
working on, and running all of them at once is rarely what you want. Each process needs its own terminal, and every
command below is run from the repository root.

| Working on               | Start                                | Reachable at                |
| ------------------------ | ------------------------------------ | --------------------------- |
| Admin UI or the REST API | API + admin UI                       | `:8000`, `:3333`            |
| Tenant administration    | sysadmin API + sysadmin UI           | `:8001`, `:3334`            |
| An agent                 | API + the agent + a UI to talk to it | `:8000`, `:3333` or `:8080` |
| Document ingestion       | pipeline                             | `:3000`                     |
| This documentation site  | docs dev server, nothing else        | `:5173`                     |

### Admin UI and REST API

```bash
cd packages/api && make run-dev
```

```bash
cd packages/web && pnpm dev
```

Uvicorn with `--reload` on port 8000 (OpenAPI docs at [http://localhost:8000/docs](http://localhost:8000/docs)) and Nuxt
on port 3333. The Nuxt dev server proxies `/api/v1` to `localhost:8000`, so the API has to be running or every request
from the UI fails. The port and the path to the repository-root `.env` are already baked into the `dev` script, so no
flags are needed.

### System administration UI and API

```bash
cd packages/sysadmin-api && make run-dev
```

```bash
cd packages/sysadmin-web && pnpm dev
```

The sysadmin plane is a separate deploy artifact and runs on its own ports: the API on 8001 and the UI on 3334.
`packages/sysadmin-web` is a Nuxt layer over `packages/web`, but it proxies `/api/v1` to `localhost:8001`, so it needs
the sysadmin API and not the main one. You do not need the main API or admin UI running to work on tenants, roles and
users.

### Agents

```bash
cd packages/agent && make run-rag-agent
```

The agent subscribes to NATS and registers itself with the platform. `packages/agent/Makefile` has a `run-*` target for
each agent in `packages/agent/app/`, so swap in `run-retrieval-agent` or `run-llm-wrapping-agent` as needed.

The agent itself only needs the Docker infrastructure. To actually send it a message you also need the API, plus either
the admin UI on 3333 or OpenWebUI on 8080.

### Document ingestion pipelines

```bash
make -C packages/pipeline document-ingestion-pipeline
```

Dagster on port 3000. The target loads `.env`, points `DAGSTER_HOME` at `~/.dagster_home` and installs
`dagster.local.yaml` there on first run, so your run history survives restarts. `make playground` and
`make -C packages/pipeline quickstart` run the SDK example pipelines instead, if that is what you are after.

Pair this with a RAG agent when you want the full retrieval loop: ingest documents through Dagster, then query them
through the agent.

### Documentation site

```bash
cd docs && pnpm install
```

```bash
cd docs && pnpm run docs:dev
```

VitePress on port 5173, with the German pages under `/de/`. This is the one thing on this page that needs neither the
Docker stack nor `make setup`: `docs/` is not a pnpm workspace member, it carries its own `pnpm-lock.yaml`, and you
install it from inside the directory rather than with a filter from the root.

::: tip First install is slow on purpose
The workspace sets `minimumReleaseAge`, so pnpm refuses any package published within the last seven days. That is
supply-chain hardening, not a broken lockfile.
:::

## Step 7: Sign in

Open [http://localhost:3333](http://localhost:3333) (or [http://localhost:3334](http://localhost:3334) for the sysadmin
UI). You are redirected to Keycloak on port 8180. Sign in with the superuser from `.env`:

- Username: `admin`
- Password: `admin`

Authentication in development goes through the bundled Keycloak rather than Azure Entra ID, so you need neither an Azure
tenant nor OAuth credentials. The credentials come from `SUPERUSER_USERNAME` and `SUPERUSER_PASSWORD` in `.env.dev`, and
the account carries the `AIHubAccess` and `AIHubSysAdmin` roles, which is what the admin UI, the sysadmin endpoints and
OpenWebUI check for. The same login works everywhere.

## Verify the setup

Check the infrastructure first, then whichever processes you started:

- `docker compose -f infra/docker-compose.dev.yml ps` shows no container in `exited` or `unhealthy`.
- [http://localhost:8000/docs](http://localhost:8000/docs) renders the API reference.
- [http://localhost:3333](http://localhost:3333) signs you in and shows the admin UI.
- [http://localhost:3334](http://localhost:3334) shows the tenant list, if you started the sysadmin pair.
- The agents list in the admin UI contains the agent you started and marks it `online`.
- Sending a message to that agent from [http://localhost:8080](http://localhost:8080) produces a reply.
- [http://localhost:6006](http://localhost:6006) shows a Langfuse trace for that exchange.

## WSL troubleshooting

**A port works in Ubuntu but not in the Windows browser.** WSL2 forwards localhost automatically, but the relay
occasionally stops after the host sleeps. `wsl --shutdown` from PowerShell fixes it. If a specific dev server stays
unreachable, bind it to all interfaces instead: `pnpm dev --host 0.0.0.0` for either frontend, or edit the `--host` flag
in the relevant make target.

**OpenWebUI on 8080 never comes up while everything else is healthy.** Host networking is off in Docker Desktop. See
[Step 2](#step-2-enable-the-wsl-backend-in-docker-desktop).

**`uv sync` is slow and hot reload never fires.** The repository is on `/mnt/c`. Move the clone into the Linux
filesystem; there is no configuration that makes the mounted path fast.

**Containers get OOM-killed or the machine freezes.** WSL is capped below what the stack needs. Raise `memory` in
`.wslconfig` and `wsl --shutdown`.

**Certificate or token errors after the laptop wakes from sleep.** WSL's clock drifts out of sync with the host and
Keycloak rejects the skewed timestamps. Run `sudo hwclock -s` inside Ubuntu, or `wsl --shutdown` and start over.

**Port conflicts on startup.** Something on the Windows side already owns 8080, 5432, 6379 or 4222. Find it with
`netstat -ano | findstr :8080` in PowerShell and stop it, or change the host-side port mapping in
`infra/docker-compose.dev.yml`.

## Next steps

With the stack running, [Your First Agent](../3_your_first_agent/) walks through building an agent against the SDK, and
[Your First Pipeline](../4_your_first_pipeline/) does the same for data ingestion.
