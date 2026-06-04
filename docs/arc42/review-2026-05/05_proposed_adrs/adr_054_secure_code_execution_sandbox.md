# Secure Code-Execution Sandbox (Harden the Jupyter Code Interpreter)

**Status**: Proposed (2026-05-29) **Severity**: P1 (security — user-supplied code execution)
**Drives**: Overview §3.1 #36 (insecure code execution), §3.1 #12 (false "sandbox" claim family); relates to §3.1 #34
(DevSecOps), §3.1 #3 (multi-tenancy)

## Context

OpenWebUI's code interpreter executes **user-supplied Python**. Verified in the compose template
(`infra/deployment/templates/docker-compose.yml.j2`):

- `CODE_EXECUTION_ENGINE: jupyter` and `CODE_INTERPRETER_ENGINE: jupyter` point at a **single shared** `jupyter-lab`
  container, authenticated by one `JUPYTER_TOKEN`, with a **shared persistent workspace** volume
  (`{volume_root}/jupyter-data:/home/jovyan/work`).
- The jupyter service is on the **`backend` network** (per the deployment CLAUDE.md network table: `backend` hosts
  `litellm`, `langfuse-*`, `mineru-api`, `vLLM`, `jupyter`, `otel`).
- There is **no** `read_only`, `cap_drop`, `security_opt` (no `no-new-privileges`/seccomp/AppArmor), **no** `pids_limit`,
  and **no** `deploy.resources.limits` (CPU/memory) on the jupyter service.
- There is **no per-user / per-tenant isolation** — every user's code runs in the same container against the same
  workspace.
- jupyter is **not** on `egress`, so executed code cannot reach the internet *directly*; but it **can reach backend
  peers** (e.g. `litellm`, which holds LLM provider API keys) and pivot through peers that do have egress
  (`playwright`, `searxng`, `docling`).

Meanwhile the platform **advertises "code execution sandbox"** as a capability strength (Overview §1, §4.2). The
hardening reality is **container-level only** — adequate for trusted single-tenant internal use, but not a hardened
sandbox for untrusted input or multi-tenant/regulated deployments.

## Decision Drivers

- **It executes arbitrary user code.** Any authenticated user holding the code-interpreter permission gets RCE inside
  the container.
- **Blast radius**: shared workspace = cross-user data exposure; backend reachability = potential LLM-key exfiltration
  / lateral movement / SSRF pivot; no resource caps = DoS of the host.
- **Truth-in-docs**: calling it a "sandbox" sets an expectation the deployment does not meet (false-claim family #12).
- **Defence in depth**, not network-only: a container is not a security boundary against hostile code.

## Decision

1. **Stronger isolation boundary.** Run user code in an ephemeral, per-session sandbox using a kernel-isolating runtime
   (gVisor / Kata) or a process jailer (nsjail/firejail) — not a long-lived shared kernel.
2. **Lock down the container.** `cap_drop: [ALL]`, `security_opt: [no-new-privileges, seccomp, apparmor]`,
   `read_only` root FS with a tmpfs scratch, `pids_limit`, and `deploy.resources.limits` (CPU/memory) + execution
   timeouts and output size caps.
3. **Network isolation.** Put the executor on a **dedicated, locked-down network** that cannot reach backend peers
   (especially `litellm`) and has **no egress**; expose only what the interpreter genuinely needs via an explicit,
   audited proxy.
4. **Per-user/tenant workspace.** Ephemeral or per-user scratch; never a shared persistent `jupyter-data` across users.
5. **Correct the docs.** Stop calling it a "sandbox" until 1–4 land; describe the actual isolation level (ties #12).
6. **Gate it.** Keep `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER` opt-in per role; log and rate-limit executions.

## Consequences

**Positive**

- User code can no longer trivially read other users' data, exfiltrate LLM keys, pivot, or exhaust the host.
- The "sandbox" claim becomes true and audit-defensible.
- Safe to expose the code interpreter in multi-tenant / regulated deployments.

**Negative**

- gVisor/Kata add runtime overhead and ops complexity; per-session kernels increase cold-start latency.
- Locking the network may break workflows that (implicitly) relied on reaching backend services.

**Open items**

- gVisor vs Kata vs nsjail given the deployment substrate (Docker Compose Gen 1/2 vs K8s Gen 3 — Gen 3 can use
  gVisor/Kata RuntimeClass + NetworkPolicy more cleanly).
- Whether to share the hardened-sandbox pattern with the Playwright browser-automation service (similar exposure).

## References

- `infra/deployment/templates/docker-compose.yml.j2` — `jupyter` service (network `backend`, no caps/limits) +
  OpenWebUI `CODE_EXECUTION_*` / `CODE_INTERPRETER_*` env.
- `infra/deployment/CLAUDE.md` — network-zone table (jupyter on `backend`).
- Overview §3.1 #36, §1 / §4.2 ("code execution sandbox" capability claim), §3.1 #12 (false-claim family), §3.1 #34
  (DevSecOps), §3.1 #3 (multi-tenancy).
- [gVisor](https://gvisor.dev/), [Kata Containers](https://katacontainers.io/), [nsjail](https://github.com/google/nsjail).
