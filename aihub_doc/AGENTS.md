# aihub_doc - Documentation & ADRs

**Purpose**: Arc42 documentation, Architectural Decision Records (ADRs), VuePress site generation.

## Scope Responsibility

Project documentation, architectural decisions, human-readable docs. NOT code (reference code elsewhere).

## Folder Structure

```
aihub_doc/
├── arc42/                     # Arc42 architecture documentation
│   ├── decisions/             # ADRs (CRITICAL for architectural changes)
│   │   └── YYYY_MM_DD_decision-summary.md
│   ├── architecture/          # System architecture docs
│   └── ...                    # Other arc42 sections
└── README.md                  # VuePress config info
```

## ADRs (Architectural Decision Records)

**Purpose**: Document significant technical decisions. Required before major changes.

**When to create ADR**:
- Adding major dependencies (frameworks, libraries)
- Introducing new tools (Dagster, Pulumi, etc.)
- Altering fundamental patterns (Service/Controller/Repository, event hierarchy, etc.)
- Changing deployment strategy
- Security/auth model changes

**ADR Format**: `/home/user/aihub-core/aihub_doc/arc42/decisions/YYYY_MM_DD_short-decision-summary.md`

**Template**:
```markdown
# Title of the Decision

Clear, concise title. Example: "Adopt Dagster for Data Pipelines"

## Context

Describe the problem or situation. What is the technical/business context?

## Decision Drivers

Key forces influencing decision (bullet points):
- Performance requirements
- Team expertise
- Ecosystem maturity
- etc.

## Decision

State your decision clearly. Describe exactly what you chose to do.

## Consequences

Results of your decision:
- **Positive**: Benefits, improvements
- **Negative**: Trade-offs, limitations
```

**Example**: `2024_03_15_adopt-dagster-for-pipelines.md`

## Consultation Protocol

**CRITICAL**: Before making significant changes, consult existing ADRs in `/home/user/aihub-core/aihub_doc/arc42/decisions/` to ensure no conflicts.

**Search for related ADRs**:
```bash
grep -r "keyword" /home/user/aihub-core/aihub_doc/arc42/decisions/
```

## Documentation Site

**Generator**: VuePress (static site from markdown)
**Build**: Generates from root `/README.md` + package `README.md` files
**Not for agents**: Human-readable docs, verbose. Agents use `AGENTS.md` files.

## Development Workflow

1. **Make significant decision**: Consult existing ADRs
2. **Create ADR**: Use template, name `YYYY_MM_DD_summary.md`
3. **Place**: `/home/user/aihub-core/aihub_doc/arc42/decisions/`
4. **Commit**: With code changes implementing decision
5. **Reference**: Link in PR description

## Quick Reference

**ADR locations**: `/home/user/aihub-core/aihub_doc/arc42/decisions/`

**Common ADR topics**:
- Framework choices (LlamaIndex, Dagster, FastAPI)
- Architectural patterns (event-driven, delegation-based processes)
- Security models (OAuth2, RBAC, permission hierarchy)
- Deployment strategies (Docker Compose, Pulumi)
- Database choices (FerretDB, Milvus, Valkey)

**Create ADR**:
1. Copy template format
2. Name: `YYYY_MM_DD_decision-summary.md`
3. Fill: Context → Drivers → Decision → Consequences
4. Place: `aihub_doc/arc42/decisions/`
5. Commit with implementing code

**Search ADRs**: `grep -r "<topic>" /home/user/aihub-core/aihub_doc/arc42/decisions/`
