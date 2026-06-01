# aihub-wpe: TLS Private Key Committed to Git — Remediation Procedure

**Status**: Proposed (2026-05-28) **Severity**: P0 (security incident — private key disclosure)
**Drives**: Overview §3.5 #1 (W*P TLS key in git);
[Details §24 ADR-NEW-041](../02_architecture_review_details.md#24-proposed-adrs-36-total)

## Context

The customer repo `aihub-wpe` (HEAD `c4b1527 2025-12-18`) tracks a TLS certificate **and its matching private
key** in the working tree:

- `aihub-wpe/wpe.ai-agents.ch+1.pem` (certificate)
- `aihub-wpe/wpe.ai-agents.ch+1-key.pem` (private key — **disclosure**)

`.gitignore` lists only `.env`; no rule covers `*.pem`, `*-key.pem`, or `secrets/`. The naming convention
(`wpe.ai-agents.ch+1*.pem`) matches the output format of `mkcert`, suggesting these were originally a local-dev
cert pair that was accidentally committed and never removed. Either way, the production subdomain `wpe.ai-agents.ch`
is the very-much-real customer hostname.

Evidence that this is a real exposure, not a benign artifact:

- The file is tracked in `git log` and has been pulled by every CI run and every developer clone since it was
  committed.
- W*P production runs Traefik + Let's Encrypt ACME (see compose), which generates its own certs at runtime — so
  the committed cert is *not* needed for production. The committed pair is dead weight, but the private key
  exposure is permanent until history is rewritten.
- The repo is `bbvch-ai/aihub-wpe`, which is internal-only on GitHub, but "internal" is not a security boundary
  — every contributor since the commit has a clone with the key.

There is currently no remediation runbook in the customer template (`aihub-{customer_id}`) or in the core
docs. This ADR documents the procedure so it can be reused if a similar disclosure happens for a future customer.

## Decision Drivers

- **Immediate exposure**: a private key in git is compromised until rotated, regardless of how "private" the
  hosting repo is.
- **History rewrite is destructive**: BFG / `git filter-repo` rewrites every contributor's clone. Coordination
  required.
- **Audit trail**: who pulled the repo while the key was tracked, and were any of those pulls onto disks now
  outside the org's control (former employee laptops, etc.).
- **Template debt**: the customer template (`aihub-{customer_id}`) should ship with a strict `.gitignore` so this
  pattern is mechanically impossible for the next customer.

## Decision

Four-step remediation, executed in this order:

1. **Rotate the cert immediately.**
   - Production W*P uses Traefik + Let's Encrypt ACME. Trigger re-issuance: delete the ACME cache (`acme.json`)
     on the prod VM, restart Traefik. New cert + new key are issued; the old key in git becomes invalid.
   - If the key was *also* used outside Traefik (manual TLS termination, mTLS clients), revoke and re-issue
     manually via `certbot revoke` or the equivalent.

2. **Add `.gitignore` rules** to the W*P repo and to the customer template:

   ```
   # TLS / secrets
   *.pem
   *-key.pem
   *.key
   *.p12
   secrets/
   .env*
   !.env.example
   ```

   Commit this change first so anyone re-cloning post-rewrite cannot accidentally re-add the keys.

3. **Rewrite git history.**
   - Run `git filter-repo --invert-paths --path wpe.ai-agents.ch+1.pem --path wpe.ai-agents.ch+1-key.pem`
     against a fresh clone (BFG is the alternative but `git-filter-repo` is the upstream-recommended tool).
   - Force-push to `main` and to every protected branch.
   - **Coordinate with all contributors**: existing clones must be discarded and re-cloned. Anyone who has
     local branches must rebase them on the rewritten history.
   - GitHub: enable secret scanning on the repo so any re-introduction is blocked at PR time.

4. **Audit pull activity.**
   - GitHub: `Settings → Audit log` for the org, filtered to `aihub-wpe` repo + clone/pull events since the key
     was committed.
   - For any pull from an account no longer with the org, treat the key as still-compromised until the
     destination disk is verified destroyed.
   - Log the audit result in the W*P customer ADR (once W*P gets its own arc42 + ADRs per §3.5 #8).

After remediation, update `aihub-{customer_id}` template repo to include the strict `.gitignore` and a
pre-commit hook running `gitleaks` or `detect-secrets` so a future customer cannot repeat this commit.

## Consequences

**Positive**

- Production cert is rotated; the committed key is dead-keyed.
- Customer template prevents recurrence by construction.
- The procedure is documented for any future incident.

**Negative**

- Force-push to `main` will break every existing clone. Communication overhead is non-trivial for a
  customer-facing repo.
- Audit may surface that the key was pulled by accounts the org cannot recover from — at which point the
  rotation in step 1 is the only mitigation.
- History rewrite invalidates any signed commits and any external tooling pinned to old commit SHAs.

**Open items**

- Whether to publish the post-rewrite procedure to the public docs site (as a generic playbook) or keep it
  in `arc42/review-2026-05` (incident-specific).
- Whether a similar audit should run preemptively on the other customer repos (B*D / C*C / Dem*scope / F*H) —
  recommend yes; this ADR's scope is W*P-specific but the playbook is reusable.
- Long-term: bring W*P off the "manual VM with hand-managed certs" pattern entirely by migrating to Gen 2 or
  Gen 3, where cert lifecycle is owned by Traefik + Let's Encrypt or cert-manager (per §3.5 #2).

## References

- Overview §3.5 #1 (the finding), §5.5 (the concern detail), §1 Summary Weaknesses (W*P TLS row).
- [git-filter-repo](https://github.com/newren/git-filter-repo) — upstream-recommended history rewrite tool.
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) — alternative.
- [GitHub Docs — Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
- [Let's Encrypt — How to issue a certificate](https://letsencrypt.org/getting-started/).
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning).
- Proposed ADR `adr_NEW-005` — Secrets Management and Rotation (this ADR is a specific instance of the broader
  policy).
