---
name: arc42
description: Write, edit, or review arc42 architecture documentation chapters in docs/arc42/chapters/. Encodes the official arc42 framework structure, section purposes, and quality criteria for all 12 chapters. Use when user says 'write arc42 chapter', 'edit arc42 documentation', 'review arc42', 'update architecture documentation', 'arc42 section X', 'improve chapter Y', 'arc42 quality check', or 'architecture documentation'. Do NOT use for ADR creation (use /document-decision), VitePress docs site pages (use /write-doc or /document-feature), or explaining existing code (use /explain).
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# arc42 Architecture Documentation

Write, edit, or review arc42 architecture documentation chapters. Takes a chapter number, chapter name, or "review" as
`$ARGUMENTS`.

## Before You Start

Read these files for context:

- **Platform overview**: `CLAUDE.md` — understand the Swiss AI Hub platform architecture (NATS, Milvus, Dagster,
  LiteLLM, Docker network zones, microservice topology)
- **Existing chapters**: Browse `docs/arc42/chapters/` to understand what's already documented
- **ADRs**: Scan `docs/arc42/decisions/` for architectural decisions that should be referenced from chapters
- **Scope CLAUDE.md files**: Each package has a `CLAUDE.md` with architecture details — use these as source material

## File Structure

Chapters live at:

```
docs/arc42/chapters/NN_chapter_name.md
```

The 12 files and their exact names:

| #   | File                             | arc42 Section            |
| --- | -------------------------------- | ------------------------ |
| 01  | `01_introduction_and_goals.md`   | Introduction and Goals   |
| 02  | `02_architecture_constraints.md` | Architecture Constraints |
| 03  | `03_context_and_scope.md`        | Context and Scope        |
| 04  | `04_solution_strategy.md`        | Solution Strategy        |
| 05  | `05_building_block_view.md`      | Building Block View      |
| 06  | `06_runtime_view.md`             | Runtime View             |
| 07  | `07_deployment_view.md`          | Deployment View          |
| 08  | `08_crosscutting_concepts.md`    | Crosscutting Concepts    |
| 09  | `09_architecture_decisions.md`   | Architecture Decisions   |
| 10  | `10_quality_requirements.md`     | Quality Requirements     |
| 11  | `11_risks_and_technical_debt.md` | Risks and Technical Debt |
| 12  | `12_glossary.md`                 | Glossary                 |

Images go in `docs/media/architecture/` (`.drawio` source files + `.png` exports).

## Mode: Write or Edit a Chapter

### Step 1: Gather Source Material

Before writing any chapter, gather real information from the codebase:

```bash
# Platform architecture
cat CLAUDE.md

# Scope-specific architecture
find . -name "CLAUDE.md" -not -path "./.claude/*" -not -path "*/node_modules/*"

# Docker services and network topology
cat docker-compose.dev.yml | head -200

# ADRs for architectural decisions
ls docs/arc42/decisions/

# Existing chapter to understand current state
cat "docs/arc42/chapters/NN_chapter_name.md"
```

Cross-reference between chapters — arc42 sections are interconnected:

- Section 1 quality goals feed into Section 4 (strategy) and Section 10 (quality requirements)
- Section 3 context boundaries define Section 5 building blocks
- Section 4 strategy decisions appear as ADRs in Section 9
- Section 5 building blocks appear in Section 6 runtime scenarios
- Section 7 deployment maps Section 5 blocks to infrastructure

### Step 2: Write Following Section-Specific Guidance

Each arc42 section has specific content requirements. Follow the guidance for the section you're working on:

______________________________________________________________________

### Section 1: Introduction and Goals

**Purpose**: Describe the driving forces — why does this system exist, who cares, and what quality attributes matter
most.

**Required subsections**:

- **1.1 Requirements Overview**: Compact summary of functional requirements and driving forces. Use activity diagrams,
  numbered lists, or BPMN. Reference existing requirements documents rather than duplicating them. Keep it to essential
  tasks and use cases — highlight business goals explicitly.

- **1.2 Quality Goals**: Table of the top 3-5 quality goals prioritized by major stakeholders. Use concrete scenarios,
  not buzzwords. Reference ISO 25010 categories. Format as prioritized table with quality goal + scenario columns. These
  goals drive ALL architectural decisions — Section 4 strategy and Section 10 details build on these.

- **1.3 Stakeholders**: Table with Role/Name | Contact | Expectations columns. Search broadly — include everyone who
  needs to know the architecture, must work with the code, requires documentation, or makes decisions. Describe their
  specific expectations of the architecture.

**Common mistake**: Writing vague quality goals like "high performance" — instead write measurable scenarios like "The
system responds to a user's RAG query within 3 seconds under normal load".

Be aware the solution is a platform consisting of multiple components (other open source projects). When Describing the
solution platform, describe it as one platform. Any requirement states always applies to the platform. Do not distribute
it to the respective component. Do not name the concrete open-source projects used.

______________________________________________________________________

### Section 2: Architecture Constraints

**Purpose**: Document where architects have NO freedom — regulations, mandates, technology constraints.

**Required subsections** (present as tables with explanations):

- **Technical constraints**: Hardware limitations, technology mandates, infrastructure decisions
- **Organizational and political constraints**: Team structure, budget, timeline, regulatory requirements
- **Conventions**: Programming guidelines, versioning, documentation standards, naming conventions

**Key principle**: Constraints are non-negotiable. If it's a preference, it belongs in Section 4 (Solution Strategy),
not here. Document the consequences of each constraint on stakeholders and design outcomes.

______________________________________________________________________

### Section 3: Context and Scope

**Purpose**: Draw the boundary — what's inside the system, what's outside, and what crosses the boundary.

**Required subsections**:

- **3.1 Business Context**: System as a black box. Show ALL external communication partners. Use a context diagram +
  table with columns: Communication Partner | Inputs | Outputs. Show data flows (not dependencies). Display external
  influences and transitive dependencies.

- **3.2 Technical Context** (optional but recommended): Map business interfaces to technical channels and protocols. Use
  UML deployment diagrams or equivalent. Show the technical realization of domain interfaces. Can be deferred to Section
  7 for leaner documentation.

**Key principle**: "Show ALL external interfaces" — omissions here cascade as blind spots through the entire
documentation. Restrict to overview level, avoid excessive detail. Explicitly note risks at external interfaces.

For Swiss AI Hub, external partners include: end users via OpenWebUI, admin users via Admin UI, cloud LLM providers via
LiteLLM, SharePoint/OneDrive via Rclone, MS Teams/Slack via bot integrations, SSO/IdP, and GitHub for CI/CD.

______________________________________________________________________

### Section 4: Solution Strategy

**Purpose**: Summarize the fundamental "why" behind architectural decisions — technology choices, decomposition
approach, and how quality goals are achieved.

**Recommended format**: Table linking quality goals to solution approaches:

| Quality Goal     | Scenario                               | Solution Approach                           | Details Link |
| ---------------- | -------------------------------------- | ------------------------------------------- | ------------ |
| Data sovereignty | No data leaves customer infrastructure | Self-hosted deployment, local LLM inference | Section 7    |

**Content categories**:

- Technology decisions (Python/FastAPI, NATS, Milvus, Dagster, etc.)
- Top-level decomposition (microservices, event-driven, SDK vs platform split)
- Quality goal achievement strategies
- Organizational decisions (monorepo, uv workspaces, Docker Compose)

**Style**: Keep it compact — keyword lists rather than lengthy prose. Cross-reference Section 5 (structure), Section 8
(concepts), Section 9 (decisions). Iterate gradually — this section evolves as the architecture matures.

______________________________________________________________________

### Section 5: Building Block View

**Purpose**: The "floor plan" — static decomposition into modules, components, and subsystems with their dependencies.
This is MANDATORY and typically the largest section.

**Hierarchical structure**:

- **Level 1**: White box of the overall system (the monorepo) containing black box descriptions of all major building
  blocks. Must be consistent with Section 3 external interfaces.
- **Level 2**: Zoom into selected Level 1 blocks (e.g., inside `packages/agent`, inside `packages/pipeline`).
- **Level 3+**: Further refinement only where architecturally relevant.

**White box template** (for each decomposition level):

- Overview diagram
- Motivation for this decomposition
- Black box descriptions of contained building blocks
- Important interfaces not covered elsewhere

**Black box template** (for each building block):

- Purpose/Responsibility
- Interface(s) with quality/performance characteristics
- Optional: fulfilled requirements, file location, open issues

**Key principle**: "Prefer relevance over completeness" — document important, surprising, risky, complex, or volatile
blocks. Use tables for efficient documentation. Map source code locations to building blocks.

For Swiss AI Hub Level 1 building blocks: `packages/core`, `packages/agent`, `packages/api`, `packages/pipeline`,
`packages/process`, `packages/web`, `packages/bot`, plus infrastructure services (NATS, Milvus, PostgreSQL, SeaweedFS,
LiteLLM).

______________________________________________________________________

### Section 6: Runtime View

**Purpose**: Show how building blocks BEHAVE — concrete scenarios with interactions, not just static structure.

**What to document** (select architecturally relevant scenarios):

- Important use cases (e.g., user asks a RAG question, document ingestion pipeline runs)
- Critical external interface interactions
- Startup, shutdown, error/exception handling
- Key architectural mechanisms (event replay, NATS pub/sub, streaming responses)

**Acceptable formats**: Numbered steps, sequence diagrams, activity diagrams, BPMN, state machines. Mermaid
`sequenceDiagram` blocks work well in markdown.

**Key principles**:

- Keep it lean — document only a few architecturally significant scenarios
- Map building block instances to activities in each scenario
- Partial scenarios are acceptable — document excerpts rather than complete flows
- Mix abstraction levels — include both fine-grained (agent event handling) and coarse (full pipeline run) scenarios

______________________________________________________________________

### Section 7: Deployment View

**Purpose**: Map software to infrastructure — what runs where, on what hardware, connected how.

**Required subsections**:

- **Infrastructure Level 1**: Overview diagram showing system distribution across environments. For Swiss AI Hub: the
  Docker Compose topology with network zones (proxy, backend, data, storage, egress). Map building blocks to containers.

- **Infrastructure Level 2**: Detailed views of selected infrastructure elements (e.g., the PostgreSQL cluster serving 4
  databases, the SeaweedFS cluster topology).

**Source material**: `docker-compose.dev.yml` defines all containers, networks, ports, and dependencies.
`deployment/templates/docker-compose.yml.j2` has production configuration.

**Multiple environments**: Document dev (Docker Compose), production (Kubernetes/Docker Swarm), and any staging
environments separately when they differ.

______________________________________________________________________

### Section 8: Crosscutting Concepts

**Purpose**: Document practices and patterns that span multiple building blocks — the "rules" that ensure consistency.

**Select from these categories** (do NOT attempt to cover all):

- Authentication and authorization (SSO, JWT, permission model)
- Logging, monitoring, observability (OpenTelemetry, Langfuse)
- Error handling patterns
- Domain/business models
- Data formats and serialization (Pydantic models, event schemas)
- Communication patterns (NATS pub/sub, Swiss AI Agent Protocol)
- Persistence approach (entity-as-repository, FerretDB)
- i18n architecture (dual frontend/backend system)
- Configuration management

**Format**: Each concept gets a level-2 heading (8.1, 8.2, etc.). Include source code examples where they clarify.
Hyperlink between building blocks (Section 5) and concepts.

**Key principle**: "Document concepts with source code!" — abstract descriptions are less useful than concrete examples
from the codebase. Restrict to the most important topics for YOUR system.

______________________________________________________________________

### Section 9: Architecture Decisions

**Purpose**: Point to the ADR directory.

**Content**: Reference the ADRs in `docs/arc42/decisions/`.

**ADR format** (documented in `docs/arc42/decisions/0000_00_00_template.md`):

- Context → Decision Drivers → Decision → Consequences
- File naming: `YYYY_MM_DD_short_decision_summary.md`

Do NOT duplicate the `/document-decision` skill's workflow — this section only points to the ADRs.

______________________________________________________________________

### Section 10: Quality Requirements

**Purpose**: Expand on Section 1.2 quality goals with detailed, measurable scenarios.

**Required subsections**:

- **10.1 Quality Tree**: Overview of quality requirements by category. Use ISO 25010:2023 or the arc42 Q42 model with 9
  dimensions: Reliable, Flexible, Efficient, Usable, Secure, Safe, Maintainable, Suitable, Operable. Format as mindmap,
  table, or quality attribute utility tree. Do not repeat quality goals from 1.2 as quality dimension.

- **10.2 Quality Scenarios**: Concrete, measurable scenarios in short form:

  - **Context/Background**: System state or environment
  - **Source/Stimulus**: What triggers the behavior
  - **Metric/Acceptance Criteria**: Measurable response measure

  Include both **usage scenarios** (runtime behavior: "RAG query returns results within 3 seconds") and **change
  scenarios** (modification effort: "Adding a new agent type requires changes in 2 files").

**Key principle**: If quality goals from Section 1.2 are vague ("high availability"), this section MUST make them
concrete and measurable. Consider usage, change, and fault/failure scenarios.

______________________________________________________________________

### Section 11: Risks and Technical Debt

**Purpose**: Honest assessment of known problems, ordered by priority.

**Content**: Prioritized list or table of:

- Known technical risks (single points of failure, technology bets, scaling bottlenecks)
- Technical debt (shortcuts taken, deprecated patterns still in use, deferred refactoring)
- Suggested mitigation measures

**Analysis approaches**:

- Stakeholder consultation for different problem perspectives
- External interface analysis for integration risks
- Source code inspection for technical debt
- Operational process examination for deployment/monitoring gaps

**Key principle**: "Risk management is project management for grown-ups" — be transparent about what could go wrong.
This section exists for management stakeholders who need to prioritize risk mitigation.

______________________________________________________________________

### Section 12: Glossary

**Purpose**: Define domain and technical terms to ensure shared understanding across all stakeholders.

**Format**: Table with Term | Definition columns. Add a Translation column if stakeholders work in multiple languages.

**Content guidelines**:

- Include Swiss AI Hub-specific terms (Agent, Pipeline, Process, Knowledge Base, Thread, Display, Run)
- Include technology terms that stakeholders may not know (NATS, Milvus, Dagster, SeaweedFS)
- Include domain terms from the Swiss AI Agent Protocol (Control Event, Display Event, hierarchical scoping)
- Keep definitions concise — one or two sentences max
- Eliminate synonyms and homonyms by establishing canonical terms
- Assign ownership for glossary accuracy

**Key principle**: "Keep the glossary compact! Avoid trivia" — only terms that stakeholders actually need clarified.

______________________________________________________________________

### Step 3: Apply Writing Standards

Follow these rules (consistent with `docs/CLAUDE.md` writing guidelines):

- **Sentence case for headings**: "How agents work", not "How Agents Work"
- **No marketing language**: Skip "powerful", "seamless", "robust", "cutting-edge"
- **No meta-commentary**: Never write "In this section, we will discuss..."
- **Paragraphs over bullet lists**: Unless a list is genuinely the clearest format
- **Verify against codebase**: Every claim about the system must be verifiable in source code, `docker-compose.dev.yml`,
  or package `CLAUDE.md` files
- **Mermaid diagrams**: Use for architecture diagrams, sequence diagrams, deployment views
- **Tables**: Use for stakeholders, constraints, quality goals, glossary entries
- **Cross-reference between sections**: Link related content (e.g., "See Section 10 for detailed quality scenarios")

### Step 4: Verify

After writing or editing a chapter:

```bash
# 1. Verify the file exists at the correct path
ls "docs/arc42/chapters/NN_chapter_name.md"

# 2. Check heading structure — should start with # Chapter Title
head -5 "docs/arc42/chapters/NN_chapter_name.md"

# 3. Check that required subsections exist for the chapter
grep '^## ' "docs/arc42/chapters/NN_chapter_name.md"

# 4. Check for cross-references to other sections
grep -c 'Section [0-9]' "docs/arc42/chapters/NN_chapter_name.md"

# 5. If diagrams were added, verify image files exist
grep -oE '\!\[.*\]\(.*\)' "docs/arc42/chapters/NN_chapter_name.md" | while read img; do
  path=$(echo "$img" | sed 's/.*(\(.*\))/\1/')
  [ ! -f "docs/arc42/chapters/$path" ] && [ ! -f "$path" ] && echo "Missing image: $path"
done
```

## Mode: Review a Chapter

When reviewing an existing chapter, check against these criteria:

### Completeness Check

For each section, verify the required subsections exist (see section-specific guidance above). Report missing
subsections.

### Quality Criteria

| Criterion                    | Check                                                                         |
| ---------------------------- | ----------------------------------------------------------------------------- |
| Required subsections present | `grep '^## ' "docs/arc42/chapters/NN_chapter_name.md"`                        |
| Concrete, not vague          | No "high performance" without measurable scenario                             |
| Cross-references             | Links to related sections where content connects                              |
| Codebase accuracy            | Claims match actual `docker-compose.dev.yml`, `CLAUDE.md`, source code        |
| Diagrams where needed        | Context diagrams (S3), building block diagrams (S5), deployment diagrams (S7) |
| No marketing language        | No "powerful", "seamless", "robust", "cutting-edge"                           |
| Tables for structured data   | Stakeholders, constraints, quality goals use tables not prose                 |
| Glossary terms defined       | Technical terms used in other chapters appear in Section 12                   |

### Section-Specific Review Checklist

- **S1**: Has quality goals table? Stakeholder table with expectations? Business goals explicit?
- **S2**: Constraints categorized (technical/organizational/conventions)? Consequences documented?
- **S3**: Shows ALL external interfaces? Business context diagram? Data flows, not dependencies?
- **S4**: Links quality goals to solution approaches? Compact keyword style?
- **S5**: Hierarchical levels? Black box descriptions? Source code locations mapped?
- **S6**: Architecturally relevant scenarios only? Building blocks mapped to activities?
- **S7**: Software-to-infrastructure mapping? Multiple environments documented?
- **S8**: Code examples included? Only essential concepts, not exhaustive? Hyperlinks to S5?
- **S9**: References ADRs in `docs/arc42/decisions/`? No duplication with S4?
- **S10**: Quality tree present? Scenarios measurable with acceptance criteria?
- **S11**: Risks prioritized? Mitigation measures suggested?
- **S12**: Terms concise? No trivia? Covers domain + technical terms?

### Review Output Format

```markdown
## arc42 Review: Chapter NN — {Chapter Name}

### Verdict: {STRONG / ADEQUATE / NEEDS WORK}

### Completeness
| Required Subsection | Present | Notes |
|---------------------|---------|-------|
| ... | Yes/No | ... |

### Quality Issues
{Specific issues with quoted lines and suggested fixes}

### Cross-Reference Gaps
{Connections to other sections that should exist but don't}

### Factual Accuracy
{Claims that don't match the codebase, with evidence}
```

## Common Mistakes

| Mistake                                              | Fix                                                          |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| Writing vague quality goals ("high availability")    | Add measurable scenario: "99.9% uptime measured monthly"     |
| Exhaustive Section 8 covering every possible concept | Select only concepts relevant to Swiss AI Hub, skip the rest |
| Section 5 listing every class and file               | Focus on architecturally relevant blocks at 2-3 levels max   |
| Section 6 documenting every API endpoint             | Select 3-5 architecturally significant scenarios             |
| Section 9 duplicating content from Section 4         | S4 = strategy summary, S9 = point to detailed ADRs           |
| Missing cross-references between sections            | S1 quality goals must appear in S4 and S10                   |
| Section 3 showing dependencies instead of data flows | Show what data crosses the boundary, not just arrows         |
| Glossary defining common programming terms           | Only define terms stakeholders genuinely need clarified      |
