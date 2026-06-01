# SDK Import Discipline (Public API Only)

**Status**: Proposed (2026-05-28) **Severity**: P1 (long-term maintainability, contracts vs internals)
**Drives**: Overview §3.2 #10 (bmd), §3.3 #17 (ctc deep-import, new in review 2026-05);
[Details §24 ADR-NEW-038](../02_architecture_review_details.md#24-proposed-adrs-36-total)

## Context

The Swiss AI Hub Core SDK is distributed as a Python package consumed via `git+ssh` tag pins from customer
repositories. The intended contract is that customers import via the public package interface:

```python
from swiss_ai_hub.core import SomeClass        # public, stable
from swiss_ai_hub.core.agent import StartEvent # scope-level public, stable
```

Internal modules under each scope are not part of the published contract and may be renamed, moved, or removed in any
release. The `__init__.py` files in each package use `TYPE_CHECKING` + `__getattr__` lazy exports to declare what is
public; anything outside that list is internal.

Review 2026-05 found two customers violating this contract by importing from internal paths:

**aihub-bmd** (`pipelines/snk_enrichment.py:2`)

- Imports an internal helper through a deep module path bypassing the package `__init__.py`.
- Survived several SDK upgrades by luck because the internal module name happened to remain stable.

**aihub-ctc** (`agents/chat_agent/chat_agent/ChatAgent.py`)

- Three deep imports against the core internals (verified 2026-05-28):
  - `from swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history import limit_chat_history`
  - `from swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard import context_sufficient_guard`
  - `from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler`
- Also: `lib/common/types/RetrievalAgentInTheLoop.py:1-4` — internal import violation already tracked in §3.3 #14.

These violations couple customer code to internal refactors of `aihub-core`. The 16-minor SDK upgrade for C*C (and 11
for B*D) is harder than necessary because the deep imports will break silently when an internal module is renamed.

No automated check exists today; the only CLAUDE.md guidance is human-readable rule #18 ("Import rules — within a
package").

## Decision Drivers

- **Contract stability**: Public API should be the only thing customers depend on.
- **Refactor freedom**: Core team must be able to rename internal modules without breaking customers.
- **Detection at PR time**: A merged violation is harder to remove than a blocked one.
- **Onboarding new customers**: First contact with the SDK should not require reading internal source.
- **Existing violations**: Need a migration window and inventory before the gate becomes enforcing.

## Decision

Adopt a three-step import-discipline policy enforced by CI:

1. **Define the public contract.** Each scope (`packages/core`, `packages/agent`, `packages/api`, `packages/pipeline`,
   `packages/bot`) declares its public symbols via `__init__.py` lazy exports. Internal modules under
   `_internal/` or any module starting with `_` are non-public by convention.

2. **Add a ruff/lint rule** (custom check or `flake8-tidy-imports`) that fails the customer build when a customer
   repository imports through a deep path. Pattern: `from swiss_ai_hub.<scope>.<deep>.<deeper> import …` is blocked;
   `from swiss_ai_hub.<scope> import …` and `from swiss_ai_hub.core import …` are allowed. Within `aihub-core` itself,
   the existing CLAUDE.md rule #18 stands (internal modules import via full path, never re-exports).

3. **Migration plan**:
   - Today: gate is in *warn* mode in `aihub-core` CI when checking customer integration tests.
   - 2026-Q3: gate becomes *blocking* for new customer code; existing violations are tracked in this ADR's appendix.
   - 2026-Q4: every existing violation is either fixed (promote internal symbol to public) or fenced with an explicit
     `# pyright: ignore[reportPrivateImport]` plus the issue number.

If a customer needs a symbol that isn't public, the correct path is: open a PR to `aihub-core` promoting it (with
tests, docstring, semver tag) and bump the customer pin after the next release.

## Consequences

**Positive**

- Customer SDK upgrades become mechanical: only public API changes can break them.
- Core team can refactor internals freely.
- Onboarding documentation can point to the public contract instead of the source tree.
- Aligns with the Python community convention (PEP 8 underscore-prefixed = private).

**Negative**

- Initial sweep is work: B*D 1 violation, C*C 4 violations, possibly others not yet audited (Dem*scope / W*P / F*H
  pending).
- Some currently-internal helpers will need to be promoted to public, which means committing to their long-term
  signature.
- Customers on older SDK versions must do a coordinated upgrade — this ADR pairs with the per-customer SDK upgrade
  plans in §3.2-§3.6.

**Open items**

- Whether to enforce the same rule on the new `aihub-sysadmin-api` / `aihub-sysadmin-web` packages (proprietary).
- Whether the lint rule should run on customer repos directly (would require core CI to checkout customer code) or in
  customer repos via a shared pre-commit config.

## References

- Overview §3.2 #10, §3.3 #14 + #17 (this ADR closes both).
- [CLAUDE.md root rule #18 — Import rules within a package](../../../../CLAUDE.md).
- `aihub-core/packages/core/swiss_ai_hub/core/subscribers/abstract_subscriber.py` — example of correct lazy-export
  pattern using `TYPE_CHECKING` + `__getattr__`.
- [PEP 8 — Public and internal interfaces](https://peps.python.org/pep-0008/#public-and-internal-interfaces).
