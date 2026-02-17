---
name: document-solution
description: "Edit solution descriptions and concept documents for public-sector AI
  platform tenders. Use when user says 'edit the solution doc', 'update tender
  document', 'fix solution description', 'update proposal section', or 'edit
  solution concept'. Requires a section path and optional edit instructions. Writes
  high-level architecture prose for procurement evaluators -- no implementation
  details."
allowed-tools: Read, Edit, Grep
---

# Solution Description / Solution Concept Editor

Edit a single section of the solution concept document for public-sector AI platform tenders. Acts as a senior proposal
writer and solution architect.

## Input Requirements

User MUST provide:
1. **Exact section path** to edit (e.g., `High-Level Architecture > Event Backbone`)
2. **Edit instructions** (optional but recommended)

If the section path is ambiguous or missing, ask the user for clarification before proceeding.

## Steps

### 1. Locate the Section

Find the target section in `/docs/1_vision_and_positioning/3_solution`. Read the surrounding context to understand the
document flow.

### 2. Verify Claims Against Code

Before writing any capability claims, check the actual codebase:
- Search for relevant code, configs, and implementations
- Only claim capabilities that are verifiable in the code
- Use `> TODO:` comments for assumptions that need verification

### 3. Edit the Section

Apply changes following the editing guardrails below.

### 4. Summarize Changes

After editing, provide a brief summary of what was changed and why.

## Editing Guardrails

- Write only **high-level solution concept** -- no implementation details
- Preserve existing headings, anchors, and local structure
- If the section exists: edit minimally for clarity, cohesion, and reuse
- If the section does not exist: create as a subsection at the most appropriate location
- Do not add unrelated content or restructure the document

## Writing Principles

- **Verifiable**: Every claim must be backed by actual code or configuration
- **Neutral prose**: Clear, concise, readable -- no marketing language
- **Audience**: Procurement evaluators and technical reviewers
- **Regulations**: Reference only when they materially affect design or operations

## Platform Context (for reference)

- Platform-model separation with vendor-neutral LLM proxy (LiteLLM)
- Event-driven architecture with NATS + JetStream
- Python (FastAPI, LlamaIndex) backend; Nuxt/Vue frontend; Dockerized
- Observability via OpenTelemetry; Langfuse for LLM specifics
- Core services: API, Agent Service, Process Service, Bot API, Ingestion Pipelines
- Multi-tenancy with per-tenant isolation; shared LLM infra
- Data sovereignty: on-premise, Swiss private cloud, or hybrid
- Security: OAuth2/SAML/LDAP; hierarchical RBAC; stateless LLM layer

## Examples

**Typical invocation**:
```
/document-solution High-Level Architecture > Event Backbone
Update to mention JetStream persistence and at-least-once delivery guarantees.
```

**Another example**:
```
/document-solution Security > Authentication
Add section about Azure AD integration with OIDC flow.
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Section path is ambiguous | Ask the user for the exact heading hierarchy |
| Cannot verify a capability claim | Add `> TODO: verify` comment and note it in the summary |
| Section does not exist yet | Create it as a subsection at the most logical location |
| Edit would require restructuring | Only edit the target section -- suggest restructuring separately |

## Done When

- Target section is edited in place using the Edit tool
- All claims are verifiable against codebase
- Summary of changes provided to the user
- No marketing language or implementation details present
