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
> possible and undocumented. The user-facing format matrix in `docs/docs/2_platform/10_chat_ui/6_coding/index.en.md` now
> records the verified set, and the sandbox has **no** diagram renderer (`cairosvg`, `mmdc`, `plantuml`, Graphviz,
> Inkscape are all absent) and no Visio library, so `.vsdx` cannot be produced at all. Re-verify both when the base tag
> is bumped.

- **Isolation** — `OPEN_TERMINAL_MULTI_USER=true` for per-user home directories; attached to a **dedicated
  `code-sandbox` network only**, whose sole residents are the sandbox and its callers (`open-webui`; AI-Hub agents as a
  follow-up). Because Docker networks are bidirectional, keeping the sandbox off `backend` is what severs lateral reach
  to the application/processing services as well as `data`/NATS. The network is `internal: true` in non-dev stages (no
  outbound internet); host port exposed only in `dev`/`local`/`build`.
- **Wiring** — OpenWebUI connects via the Integrations env `TERMINAL_SERVER_CONNECTIONS` (bearer auth with
  `OPEN_TERMINAL_API_KEY`), replacing the Jupyter `CODE_EXECUTION_*` / `CODE_INTERPRETER_*` engine variables.
- **Scope — plain LLM models only.** OpenWebUI orchestrates Open Terminal through native `execute_code` tool-calling;
  the existing `/openai` proxy passes `tools`/`tool_calls` through transparently for plain models, and all LiteLLM
  text-generation models declare `supports_function_calling: true`. Native function calling must be enabled per model.
- **AI-Hub agent chats are deferred.** Agent surfaces (the `aihub_pipeline.py` `Pipe` and the agent branch of the
  `/openai` proxy) own their own generation and do not expose OpenWebUI-orchestrated tool-calling, so Open Terminal does
  not engage for them. Supporting agents requires the OpenAI tool-calling handshake inside the agent framework and is
  tracked as a separate follow-up — consistent with #1117's "code execution invoked from our own agents (covered
  separately)".
- **Jupyter is retained** for now (its full removal is a follow-up once any remaining consumers migrate), but OpenWebUI
  no longer uses it.

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
