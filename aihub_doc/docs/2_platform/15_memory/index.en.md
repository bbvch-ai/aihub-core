---
title: Memory
---

# Agent memory

AI agents need context to provide relevant, personalized assistance. Without memory, agents start every conversation
fresh, forcing you to repeatedly explain your preferences, working style, and organizational context. The Swiss AI Hub's
memory system enables agents to learn and retain information across conversations.

## Why memory matters

Memory enables capabilities that stateless agents can't provide. An agent learns that you prefer concise code examples
in Python, then automatically adjusts future responses to match your working style. When one user corrects an agent
about a company policy, that correction benefits everyone – all agents immediately work from the updated information.
You explain your project structure once, and agents remember it for all future interactions. Information survives
employee turnover; when team members leave, their documented knowledge remains accessible to agents serving new
employees.

## Two types of memory

The platform uses two distinct memory types:

**User memory** stores personal preferences and individual context. This memory is private to you. When an agent learns
that you prefer detailed explanations or work primarily in a specific technology stack, that information remains yours
alone.

**Organization memory** stores shared knowledge accessible to all users within your organization. Company policies,
project details, team conventions, and factual information belong here. When one user documents that "Project Falcon
uses microservices architecture," all agents can leverage that knowledge to assist any team member working on that
project.

This structure balances individual personalization with organizational consistency. Agents adapt to each user's
preferences while maintaining a common understanding of company-wide facts.

## How memory works

### Automatic learning

User memory requires no manual effort. Agents automatically extract relevant information from your conversations. As you
chat with a code assistant about Python projects, it learns your language preference. As you discuss deadlines with a
process assistant, it learns your approval patterns.

Each agent type learns differently. A code assistant focuses on technical preferences and working styles. A knowledge
retrieval agent learns about your areas of interest and preferred information formats.

### Explicit documentation

Organization memory works differently. Because this knowledge affects all users, the platform requires explicit
documentation rather than automatic inference. You choose what information to preserve as organizational knowledge.

This design prevents errors from propagating across the organization. An agent won't accidentally turn a one-time
comment into permanent company policy.

### Transparency

The platform maintains full visibility into what agents remember. Every memory includes the conversation thread where it
originated, the agent that created it, and the exact timestamp. When an agent uses a memory to inform its response, that
usage is logged and visible in the conversation trace. Through the Swiss AI Agent Protocol, all memory operations
integrate with the platform's observability system.

You can see exactly what agents remember about you, where that information came from, and when it's being used.

## Your control over memory

### Managing user memory

You have complete control over your personal memories. Access the User Memory service to see everything agents have
learned about you. You can edit any memory to correct or refine what agents remember, delete specific memories, or
delete all user memories entirely.

The platform respects data sovereignty and GDPR requirements. You can exercise your right to be forgotten by deleting
all user memories with a single action.

### Managing organization memory

Organization memory follows a similar pattern with one key difference: changes affect all users. When you edit or delete
an organization memory, you're modifying knowledge that other team members' agents rely on.

Access to organization memory management is typically restricted to administrators or knowledge managers who understand
the impact of their changes.

## Getting started

Navigate to the **User Memory** service in the platform interface. You'll see all the information agents have learned
about your preferences and working style. Each memory shows the remembered information, when it was learned, which agent
created it, and the conversation thread where it originated. Try editing a memory to see how agents adapt to your
corrections.

Access the **Organization Memory** service to view your organization's shared knowledge – company policies, project
information, and team conventions that all agents use. If you have appropriate permissions, you can contribute new
organizational knowledge or update existing information.

During conversations with agents, observe the display events to see when agents retrieve and use memories. This
transparency shows you exactly how memory influences agent responses.

## Privacy and data sovereignty

The memory system adheres to Swiss data sovereignty principles. Your personal memories are never visible to other users.
Organization memories are scoped to your tenant, preventing information leakage between different organizations using
the platform. Large organizations can further isolate organization memories by department or team.

Both memory types support full CRUD operations (create, read, update, delete), ensuring compliance with data protection
regulations. All memory data remains on Swiss-based infrastructure with the same data protection guarantees as the rest
of the platform.
