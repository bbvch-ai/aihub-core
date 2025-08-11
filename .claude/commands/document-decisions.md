# Document Architecture Decisions - Capture the "Why" Behind Your Design

You've made some significant changes to the codebase. But did you make any architecture decisions that future developers
need to understand? This cookbook guides you through documenting important technical decisions using our ADR (
Architecture Decision Records) process.

Focus on: $DECISION

## Overview

Here's your explanation documentation journey:

1. Review your changes against main
2. Check existing architecture decisions
3. Identify if you made significant architecture choices
4. Document new decisions properly
5. Reference any superseded decisions

## Your Decision Documentation Cookbook

### Step 1: Analyze Your Changes

First, let's see what you've actually changed:

```bash
# Get a comprehensive view of your changes
git diff main...HEAD

# Focus on structural changes
git diff main...HEAD --name-only | grep -E '\.(py|yml|yaml|json|toml|ts|js)$'

# Look for new directories or major file additions
git diff main...HEAD --name-status | grep '^A'
```

Look for patterns that suggest architecture decisions:

- New packages or dependencies added
- New design patterns introduced
- Major refactoring of existing structures
- Changes to how components communicate
- New technology integrations

### Step 2: Review Existing Decisions

Before documenting anything new, understand what's already decided:

```bash
# Navigate to the decisions directory
cd aihub_doc/arc42/decisions/

# List alexisting decision files
ls -la *.md | grep -v template

# Read relevant existing decisions
cat 2024_12_18_pulumi_as_iac.md
# Continue reading others that might relate to your work
```

Ask yourself:

- Do any existing decisions relate to my changes?
- Am I following or contradicting any existing decisions?
- Has my implementation made any existing decision obsolete?

### Step 3: Identify What Needs Documentation

** REQUIRES an ADR - Significant Architecture Decisions:**

- **Technology Choices**
- Adopting a new framework or library (e.g., "Use Celery for async tasks")
- Choosing between competing technologies (e.g., "Redis vs. RabbitMQ for queuing")
- Selecting a new database or storage solution

- **Architecture Patterns**
- Introducing new design patterns (e.g., "Implement Event Sourcing for audit trails")
- Changing communication patterns (e.g., "Move from REST to GraphQL")
- Adopting new architecture styles (e.g., "Transition to microservices")

- **Major Structural Changes**
- Reorganizing package structure fundamentally
- Changing how components interact
- Introducing new layers or boundaries

- **Cross-Cutting Concerns**
- New security approaches (e.g., "Implement Zero Trust architecture")
- Performance optimization strategies (e.g., "Add caching layer with Redis")
- Observability decisions (e.g., "Adopt OpenTelemetry for tracing")

- **Integration Decisions**
- How to integrate with external systems
- API versioning strategies
- Data synchronization approaches

** DOES NOT Require an ADR - Implementation Details:**

**Regular Feature Development**

- Adding a new endpoint to an existing API
- Creating a new agent following existing patterns
- Implementing business logic within established architecture

**Bug Fixes and Minor Improvements**

- Fixing a race condition
- Optimizing a query
- Refactoring a single class

**Following Existing Patterns**

- Creating a new pipeline similar to existing ones
- Adding another notification type to existing system
- Extending current functionality

**Code Quality Improvements**

- Adding type hints
- Improving test coverage
- Refactoring for readability

### Step 4: Understand the "Why"

If you've identified a decision that needs documentation, dig deep into the reasoning.

Questions to answer:

- What problem were you solving?
- What alternatives did you consider?
- Why did you choose this approach over others?
- What trade-offs did you accept?

### Step 5: Write Your ADR

Time to document! Create your decision file:

```bash
# Navigate to the decisions directory
cd aihub_doc/arc42/decisions/

# Create your ADR with today's date
# Format: YYYY_MM_DD_short_decision_summary.md
touch "$(date +%Y_%m_%d)_your_decision_summary.md"
```

Now write your ADR following this structure:

```markdown
# Title of the Decision

A clear, concise title. Example: "Adopt Redis for Caching"

## Context

Describe the problem or situation that necessitates this decision.
What is the technical business context?

## Decision Drivers

List the key forces influencing your decision as bullet points. These are the "whys".

- Performance requirements
- Scalability needs
- Team expertise
- Cost considerations
- Security requirements

## Decision

State your decision clearly and unambiguously.
Describe exactly what you have chosen to do.

## Consequences

Describe the results of your decision.
List both positive outcomes and any negative trade-offs.
```

### Step 6: Reference Superseded Decisions

If your decision replaces or modifies an existing one:

```markdown
## Context

[Your context...]

This decision supersedes the previous decision documented in
`2023_05_15_old_approach.md` due to [reason for change].

## Decision

[Your new decision...]

The approach outlined in `2023_05_15_old_approach.md` is no longer
valid because [specific reasons].
```

### Step 7: Validate Your ADR

Before finalizing, ensure your ADR is valuable:

**Quality Checklist:**

- [ ] Title clearly states the decision
- [ ] Context explains the "why" comprehensively
- [ ] Decision drivers are specific and measurable
- [ ] The decision is stated unambiguously
- [ ] Consequences include both pros and cons
- [ ] Any superseded decisions are referenced
- [ ] Future developers will understand your reasoning

**Red Flags to Fix:**

- Vague statements like "for better performance"
- Missing alternatives that were considered
- No mention of trade-offs
- Decisions that are too implementation-specific

### Examples to Guide You

**Good ADR Title:** "Adopt NATS for Inter-Service Communication"  
**Poor ADR Title:** "Update Message System"

**Good Context:** "Our current HTTP-based service communication creates tight coupling and lacks resilience. We need
asynchronous messaging to handle service failures gracefully."  
**Poor Context:** "We need better messaging."

**Good Decision Driver:** "Must handle 10,000 messages/second with <100ms latency"  
**Poor Decision Driver:** "Need fast messaging"

## Common Pitfalls to Avoid

- **Don't document every change** - Only significant architecture decisions
- **Don't be vague** - Be specific about problems and solutions
- **Don't hide trade-offs** - Be honest about disadvantages
- **Don't forget the context** - Future readers need the full picture

## You're Done When...

- You've reviewed all your changes for architecture significance
- You've checked existing ADRs for conflicts or relationships
- Any significant decision has a well-written ADR
- Your ADR explains the "why" clearly enough for someone in 2 years
- Trade-offs and consequences are honestly documented
- The file is named correctly and placed in `aihub_doc/arc42/decisions/`

Remember: Good architecture documentation is a love letter to your future self and your teammates!