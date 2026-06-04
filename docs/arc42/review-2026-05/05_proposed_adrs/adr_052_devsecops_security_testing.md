# DevSecOps Security Testing & Verification Process (SAST + DAST + Threat Modeling + Dependency/CVSS + SBOM)

**Status**: Proposed (2026-05-29) **Severity**: P1 (application security, audit readiness)
**Drives**: Overview §3.1 #34 (no recurring security testing), §3.1 #15 (supply-chain SBOM/scan), §3.1 #30
(remediation SLA); §6.2 Security pillar, §17 STRIDE

## Context

Security testing today is **point-in-time and tooling-light**, verified by reading `.github/` (2026-05-29):

- The **only** automated security mechanism in CI is **Dependabot** (`.github/dependabot.yml`). There is **no** CodeQL
  or other **SAST**, **no DAST**, no `trivy` / `semgrep` / `bandit` / `pip-audit`, and **no SBOM** generation.
- A **STRIDE threat model** was produced once for this review (§17) but there is **no refresh cadence** and no trigger
  to re-run it when the architecture changes.
- There is **no periodic penetration test**, **no CVSS scoring/triage process**, and **OWASP Dependency-Check** is not
  defined. Remediation timelines are proposed separately (§3.1 #30) but without a scoring input to prioritise them.
- §11 QA gaps and §6.2 confirm: "No SAST / dep vuln scan / SBOM / image signing / container vuln scan".

So the platform has a **detection-and-process gap** distinct from the supply-chain *artifacts* gap (#15) and the
*remediation SLA* (#30): there is no standing **process** that repeatedly tests the running application and its
dependencies and feeds a prioritised triage.

## Decision Drivers

- **Vulnerabilities sit undetected** without recurring SAST/DAST and dependency scanning.
- **Audit readiness** (ISO 27001, SOC2) expects a documented, repeatable secure-SDLC, not a one-off threat model.
- **Prioritisation needs CVSS** — remediation SLAs (#30) are meaningless without a severity score to attach them to.
- **Sovereignty/OSS posture** favours OWASP-stack tooling (Dependency-Check, ZAP, CycloneDX) that is self-hostable.

## Decision

Define and implement a DevSecOps security-testing process:

1. **SAST in CI** — CodeQL (or semgrep) for Python/TS + `bandit` for Python; fail on high-severity findings.
2. **DAST in CI/staging** — OWASP ZAP baseline scan against a deployed staging stack (auth, API, OpenWebUI).
3. **Dependency scanning** — OWASP **Dependency-Check** + `pip-audit` (Python) + `trivy` (containers), in addition to
   Dependabot version updates already present.
4. **SBOM** — generate **CycloneDX** (OWASP) SBOMs per image/release (closes the SBOM half of #15); attach to releases.
5. **CVSS triage** — score every finding (CVSS v3.1/4.0); route by severity into the remediation SLA from #30
   (critical 7d / high 30d / medium 90d).
6. **Threat-model refresh cadence** — re-run STRIDE (§17) on a schedule and on significant architecture changes; track
   as-code.
7. **Periodic penetration test** — schedule an external pentest before major customer onboarding / annually.
8. **Image signing** — `cosign` provenance (the signing half of #15).

## Consequences

**Positive**

- Continuous, repeatable security verification; vulnerabilities caught in CI, not in production.
- CVSS scoring makes the #30 remediation SLA enforceable and auditable.
- CycloneDX SBOM + signing close the supply-chain artifact gap (#15) with an OWASP-aligned, self-hostable stack.
- A documented secure-SDLC supports ISO 27001 / SOC2 audits.

**Negative**

- CI time/cost increases (SAST/DAST/scan stages); DAST needs a deployable staging target.
- External pentest is a recurring budget item.
- Initial finding backlog may be large; needs a triage runway.

**Open items**

- CodeQL vs semgrep (cost/coverage); managed vs self-hosted ZAP.
- Pentest cadence (annual vs per-major-customer) and vendor.
- Overlap management with #15 (artifacts) and #30 (SLA) — this ADR owns the *process*, those own *artifacts* and *SLA*.

## References

- `.github/dependabot.yml` (the only current automated security mechanism), `.github/workflows/` (no SAST/DAST/SBOM).
- Overview §3.1 #34, #15, #30; §6.2 Security pillar; §17 STRIDE threat model.
- OWASP [Dependency-Check](https://owasp.org/www-project-dependency-check/), [ZAP](https://www.zaproxy.org/),
  [CycloneDX](https://cyclonedx.org/); [CodeQL](https://codeql.github.com/); [CVSS](https://www.first.org/cvss/).
- Related: `adr_029` (container supply chain security), `adr_005` (secrets management & rotation).
