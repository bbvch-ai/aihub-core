# OpenWebUI Code Execution via Open Terminal (replacing Jupyter)

## Context

OpenWebUI's code execution and code interpreter features ran through the **Jupyter** service
(`minimal-notebook`). Three problems motivated a change (issue #1117):

- **Weak isolation.** Jupyter sits on the `backend` network alongside application services and executes user code in a
  single, shared kernel. The network isolation policy permits `backend → data`, so a successful container breakout has a
  path toward NATS and the databases — an unacceptable blast radius for arbitrary user-submitted code.
- **No file delivery.** The Jupyter engine has no mechanism to hand a generated file (doc/excel/pdf) to the end user;
  the model emits `sandbox:/…` links that do not resolve, so files were only reachable from the Jupyter UI.
- **Upstream direction.** OpenWebUI now classifies Jupyter as a *legacy* code-execution engine and recommends
  **Open Terminal**, its sandboxed, natively-integrated runtime with a file browser.

## Decision Drivers

- *Isolation / least privilege* — the code-execution sandbox must not be able to reach NATS or the databases, and should
  isolate users from one another.
- *File delivery* — end users must be able to download generated artifacts.
- *OpenWebUI-native, maintained path* — prefer the supported integration over the deprecated engine.
- *Reproducible, air-gap-friendly* — no outbound internet at runtime; required libraries baked into the image.

## Decision

Route OpenWebUI's code-execution path to a new **`open-terminal`** service:

- **Image** — a project-managed `open-terminal-office:0.11.34`, built `FROM ghcr.io/open-webui/open-terminal:0.11.34`
  plus `reportlab` and `fpdf2` (the base already ships pandas, openpyxl, python-docx, weasyprint, matplotlib,
  xlsxwriter). All libraries install from binary wheels at build time, so the running container needs **no outbound
  internet**. Published out-of-band like the postgres/playwright images
  (`make -C infra/deployment build-and-push-open-terminal-image`).
- **Isolation** — `OPEN_TERMINAL_MULTI_USER=true` for per-user home directories; attached to the **`backend` network
  only** (no `data`/NATS path — verified: NATS is unreachable from the container); host port exposed only in
  `dev`/`local`/`build`.
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

- **Positive** — the code-execution sandbox can no longer reach NATS/databases and isolates users per home directory;
  generated files are downloadable via Open Terminal's file browser; the integration is the OpenWebUI-native, maintained
  path; the image is reproducible and requires no outbound internet to function (libraries are baked in at build time).
- **Trade-offs**
  - Only plain-LLM chats gain code execution this iteration (agent support deferred); native function calling must be
    enabled per model and multi-step reliability varies by model.
  - **Lateral reach within `backend`.** "No NATS/database access" holds, but a sandbox breakout can still reach other
    `backend` services (LiteLLM, vLLM, MinerU, Speaches, Presidio, OTEL) over their internal ports. A dedicated
    code-sandbox network attached only to `open-webui ↔ open-terminal` would make it a true single-tenant zone —
    tracked as a follow-up.
  - **"No egress" is an image property, not a network guarantee.** The image needs no internet, but in `dev` the
    `backend` network is non-internal, so code in the sandbox can still reach the public internet. Egress can be
    firewalled per-deployment via `OPEN_TERMINAL_ALLOWED_DOMAINS` if required.
  - **Cross-user side channels.** `OPEN_TERMINAL_MULTI_USER=true` isolates per-user *files*, but users still share CPU,
    memory, `/tmp`, and the process list on one host — accepted under the current threat model.
  - **`/home` persistence.** `${VOLUME_ROOT}/open-terminal:/home` accumulates per-user artifacts on the host with no
    retention/quota policy yet — a janitor/TTL is a follow-up.
  - The image is ~1.19 GB; the Jupyter container keeps running, unused, until a later cleanup. See network isolation
    (`2025_12_22_docker_network_isolation.md`).
