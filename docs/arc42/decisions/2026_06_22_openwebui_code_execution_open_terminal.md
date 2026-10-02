# OpenWebUI Code Execution via Open Terminal (replacing Jupyter)

## Context

OpenWebUI's code execution and code interpreter features ran through the **Jupyter** service (`minimal-notebook`). Three
problems motivated a change (issue #1117):

- **Weak isolation.** Jupyter sits on the `backend` network alongside application services and executes user code in a
  single, shared kernel. The network isolation policy permits `backend → data`, so a successful container breakout has a
  path toward NATS and the databases — an unacceptable blast radius for arbitrary user-submitted code.
- **No file delivery.** The Jupyter engine has no mechanism to hand a generated file (doc/excel/pdf) to the end user;
  the model emits `sandbox:/…` links that do not resolve, so files were only reachable from the Jupyter UI.
- **Upstream direction.** OpenWebUI now classifies Jupyter as a *legacy* code-execution engine and recommends **Open
  Terminal**, its sandboxed, natively-integrated runtime with a file browser.

## Decision Drivers

- *Isolation / least privilege* — the code-execution sandbox must not be able to reach NATS or the databases, and should
  isolate users from one another.
- *File delivery* — end users must be able to download generated artifacts.
- *OpenWebUI-native, maintained path* — prefer the supported integration over the deprecated engine.
- *Reproducible, air-gap-friendly* — no outbound internet at runtime; required libraries baked into the image.

## Decision

Route OpenWebUI's code-execution path to a new **`open-terminal`** service:

(the base already ships pandas, openpyxl, python-docx, weasyprint, matplotlib, xlsxwriter)

> **Amendment 2026-08-28 — the baked-in inventory is larger than this decision recorded.** Verified against the running
> `open-terminal-office:0.11.34` container, the base image also ships **`python-pptx`, `pypdf`, `Pillow`, `numpy`,
> `scipy`, `lxml` and `PyYAML`, plus the `ffmpeg` and `pandoc` binaries**. This is not a change of decision — nothing
> was added to the image — but the omission understated the capability: PPTX, video and audio generation were all
> possible and undocumented. The user-facing format matrix in
> `docs/docs/2_platform/10_chat_ui/13_file_generation/index.en.md` records the verified set, and the sandbox has **no**
> diagram renderer (`cairosvg`, `mmdc`, `plantuml`, Graphviz, Inkscape are all absent) and no Visio library, so `.vsdx`
> cannot be produced at all. Re-verify both when the base tag is bumped.

- **Isolation** — `OPEN_TERMINAL_MULTI_USER=true` for per-user home directories; attached to a **dedicated
  `code-sandbox` network only**, whose sole residents are the sandbox and its callers (`open-webui`; AI-Hub agents as a
  follow-up). Because Docker networks are bidirectional, keeping the sandbox off `backend` is what severs lateral reach
  to the application/processing services as well as `data`/NATS. The network is `internal: true` in non-dev stages (no
  outbound internet); host port exposed only in `dev`/`local`/`build`.
- **Wiring** — OpenWebUI connects via the Integrations env `TERMINAL_SERVER_CONNECTIONS` (bearer auth with
  `OPEN_TERMINAL_API_KEY`), replacing the Jupyter `CODE_EXECUTION_*` / `CODE_INTERPRETER_*` engine variables.
- **Scope — plain LLM models only.** OpenWebUI orchestrates Open Terminal through native `execute_code` tool-calling
  (*corrected — see the amendment below*); the existing `/openai` proxy passes `tools`/`tool_calls` through
  transparently for plain models, and all LiteLLM text-generation models declare `supports_function_calling: true`.
  Native function calling must be enabled per model.
- **AI-Hub agent chats are deferred.** Agent surfaces (the `aihub_pipeline.py` `Pipe` and the agent branch of the
  `/openai` proxy) own their own generation and do not expose OpenWebUI-orchestrated tool-calling, so Open Terminal does
  not engage for them. Supporting agents requires the OpenAI tool-calling handshake inside the agent framework and is
  tracked as a separate follow-up — consistent with #1117's "code execution invoked from our own agents (covered
  separately)".
- **Jupyter is retained** for now (its full removal is a follow-up once any remaining consumers migrate), but OpenWebUI
  no longer uses it.

> **Amendment 2026-08-28 — the sandbox is not reached through `execute_code`.** The *Scope* bullet above names the wrong
> mechanism. Verified against the OpenWebUI 0.9.5 source in the running container: the built-in `execute_code` tool
> (`tools/builtin.py`) handles only the `pyodide` and `jupyter` engines and errors on anything else, and
> `CODE_INTERPRETER_ENGINE` defaults to `pyodide` and is set in no compose file. Open Terminal is reached through the
> **terminal-server integration** instead, which resolves the sandbox's OpenAPI operations into model-callable tools
> (`run_command`, `write_file`, `display_file`, …) via `get_terminal_tools` in `utils/tools.py`, gated on a terminal
> being selected in the chat and on the model's terminal capability. The rest of the bullet stands: native function
> calling must still be enabled per model, because only then are those tools passed as real function definitions rather
> than through OpenWebUI's single prompt-based tool-selection pass.

## Consequences

- **Positive** — the code-execution sandbox sits alone in `code-sandbox` and can reach only its callers, so a breakout
  reaches neither NATS/databases nor the other `backend` services (LiteLLM, vLLM, MinerU, Speaches, Presidio, OTEL); it
  isolates users per home directory; generated files are downloadable via Open Terminal's file browser; the integration
  is the OpenWebUI-native, maintained path; the image is reproducible and requires no outbound internet to function
  (libraries are baked in at build time).
- **Trade-offs**
  - Only plain-LLM chats gain code execution this iteration (agent support deferred); native function calling must be
    enabled per model and multi-step reliability varies by model.
  - **Agents become a bridge node (future).** When the agents service later joins `code-sandbox` to use the sandbox, it
    will sit on `code-sandbox` + `backend` + `data`. At the network layer the sandbox still cannot ride *through* an
    agent to `backend`, but a compromised agent process would be a pivot point — so `code-sandbox` membership is kept
    minimal (sandbox + callers only).
  - **Dev stays non-internal.** `code-sandbox` is `internal: true` only in non-dev stages; in `dev` it is non-internal
    for localhost access, so the no-internet / no-lateral-reach guarantees apply to `local`/`build`/`nightly`/`latest`,
    not `dev`. Egress can additionally be firewalled per-deployment via `OPEN_TERMINAL_ALLOWED_DOMAINS` if required.
  - **Single shared container, per-user isolation only.** `OPEN_TERMINAL_MULTI_USER=true` gives each user a separate
    Linux account and home directory with standard filesystem permissions, but it is **one shared container** — all
    users share the same kernel, CPU, memory, `/tmp`, and process list. This is a convenience for small, trusted groups,
    not a hard multi-tenant boundary; a container-per-user model would be required for that. Accepted under the current
    threat model.
  - **`/home` persistence and unbounded growth.** `${VOLUME_ROOT}/open-terminal:/home` accumulates per-user artifacts on
    the host with no retention/quota policy yet, so disk usage grows over time — operators must monitor and prune
    manually until a janitor/TTL is added (a follow-up).
  - The image is ~1.19 GB; the Jupyter container keeps running, unused, until a later cleanup. See network isolation
    (`2025_12_22_docker_network_isolation.md`).
- **Deployment prerequisite** — publish `open-terminal-office:0.11.34` to ghcr **before any non-dev stage pulls it**
  (`make -C infra/deployment build-and-push-open-terminal-image`). `nightly`/`latest` pull this exact tag; if it is
  absent, `open-webui`'s `depends_on: open-terminal (service_healthy)` gate fails and the stack will not start. Bump the
  tag deliberately and re-publish whenever the base tag or baked-in libraries change.
- **Licensing** — Open Terminal is **MIT** (standard, OSI-approved; no branding clause and no end-user threshold). This
  is distinct from `open-webui`, whose modified-BSD "Open WebUI License" carries the branding/≤50-user clause — that
  obligation comes from open-webui, not from adding this sandbox.

> **Amendment 2026-09-10 — Jupyter has been removed.** The follow-up cleanup anticipated above is done: the `jupyter`
> service, its `JUPYTER_TOKEN`/`JUPYTER_URL` variables, the `minimal-notebook` image pin, and its license entry are gone
> from the compose template and all generated stages. Open Terminal is now the only code-execution runtime in the stack.

> **Amendment 2026-10-02 — our agents use the sandbox.** The deferred agent support is done (#1570), and only the
> Universal Agent joins `code-sandbox`; the other agents stay off it. It sits on `code-sandbox`, `backend`, `data` and
> `storage`, which is the bridge-node position described above. The sandbox still reaches only its callers, so sandboxed
> code reaches nothing it could not reach before: it is not put on any other network, holds no storage credentials, and
> the agent fetches and stores the files itself. Agents call the sandbox's API rather than OpenWebUI's terminal
> integration, so each call is traced and checked against the asking user like any other agent step:
>
> - **The user's own home.** The sandbox keys homes by the `X-User-Id` header and falls back to a shared `/home/user`
>   without one, so every agent call sends the user's OpenWebUI id. The group sync records the id it matches for each of
>   our users (`OpenWebuiAccountEntity`), which puts agent work in the same home the user's chats and Files panel see.
>   The sandbox keeps only the first 8 alphanumeric characters of that id as the account name, so two users whose ids
>   share them would share a home; OpenWebUI's UUIDs make that unlikely but not impossible.
> - **A folder per conversation.** Agents work in `~/conversations/<thread>/`, where the conversation's attached files
>   are placed once before the first call. Every write goes through the sandbox's API, never through the volume, so the
>   home stays the only place sandbox files are written (see #2031 for mirroring it to our storage).
> - **Files shown to the user are copied out.** A file the model displays is read through the sandbox's raw file
>   endpoint (`GET /files/view`, which returns binary documents that `/files/read` refuses), stored in the `agent-files`
>   bucket and registered by the pipe as an OpenWebUI file on the answer, so the attachment outlives the sandbox file.
>   `/files/view` is not in the sandbox's published schema; upgrades of `open-terminal` must keep it.
>
> The *Dev stays non-internal* bullet above names `OPEN_TERMINAL_ALLOWED_DOMAINS` for egress control; open-terminal
> 0.11.34 has no such setting, so egress outside dev rests on `code-sandbox` being internal.

> **Amendment 2026-10-02 — the API joins the sandbox network; the homes are mirrored.** User Knowledge (#1936) lets each
> user browse and change their own sandbox home through our API, which joins `code-sandbox` as a further caller and sends
> only paths inside the user's home, as that user's OpenWebUI id. A file attached in an agent chat is placed in that
> conversation's folder by the API once the upload is validated. The homes are copied one way into the `sandbox-files`
> bucket by a `sandbox-mirror` sidecar (#2031): it reads the homes volume read-only, skips links instead of following
> them, uses an S3 identity limited to that bucket, and is on `backend` only, never on `code-sandbox`, so sandboxed
> code has no path to it or to its credentials. What the sandbox deleted is kept under `.deleted/` for a week. The
> volume stays the only place sandbox files are written, so a one-way copy is enough.

